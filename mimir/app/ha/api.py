"""REST API client for Home Assistant."""

from __future__ import annotations

import os
from typing import Any

import aiohttp

from ..utils.logging import get_logger
from .types import EntityState, Service

logger = get_logger(__name__)


class HomeAssistantAPIError(Exception):
    """Raised when an API call fails."""

    def __init__(self, status: int, message: str) -> None:
        self.status = status
        self.message = message
        super().__init__(f"HA API Error ({status}): {message}")


class HomeAssistantAPI:
    """REST API client for Home Assistant.

    When running as an add-on, uses the Supervisor proxy at http://supervisor.
    Otherwise, connects directly to the Home Assistant instance.
    """

    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
    ) -> None:
        """Initialize the API client.

        Args:
            url: Home Assistant URL. If None, auto-detects.
            token: Access token. If None, uses SUPERVISOR_TOKEN.
        """
        # Detect add-on environment
        supervisor_token = os.environ.get("SUPERVISOR_TOKEN")

        if supervisor_token and not url:
            # Running as add-on with token - use Supervisor proxy
            self._base_url = "http://supervisor/core/api"
            self._token = supervisor_token
            logger.info("Using Supervisor API proxy")
        elif not url:
            # Running as add-on without token - try internal Docker network
            # The 'homeassistant' hostname is available on the Docker network
            self._base_url = "http://homeassistant:8123/api"
            self._token = supervisor_token or ""
            logger.info("Using internal Docker network: %s", self._base_url)
        else:
            # Explicit URL provided
            self._base_url = f"{url.rstrip('/')}/api"
            self._token = token or ""
            logger.info("Using direct API connection: %s", self._base_url)

        self._session: aiohttp.ClientSession | None = None

    @property
    def _headers(self) -> dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure we have an active session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> Any:
        """Make an API request."""
        session = await self._ensure_session()
        url = f"{self._base_url}/{endpoint.lstrip('/')}"

        logger.debug("%s %s", method, url)

        try:
            async with session.request(
                method,
                url,
                headers=self._headers,
                json=data,
            ) as response:
                if response.status >= 400:
                    text = await response.text()
                    raise HomeAssistantAPIError(response.status, text)

                if response.content_type == "application/json":
                    return await response.json()
                return await response.text()

        except aiohttp.ClientError as e:
            raise HomeAssistantAPIError(0, str(e)) from e

    async def get(self, endpoint: str) -> Any:
        """Make a GET request."""
        return await self._request("GET", endpoint)

    async def post(self, endpoint: str, data: dict[str, Any] | None = None) -> Any:
        """Make a POST request."""
        return await self._request("POST", endpoint, data)

    async def delete(self, endpoint: str) -> Any:
        """Make a DELETE request."""
        return await self._request("DELETE", endpoint)

    # High-level API methods

    async def ping(self) -> bool:
        """Check if Home Assistant is reachable."""
        try:
            await self.get("")
            return True
        except HomeAssistantAPIError:
            return False

    async def get_config(self) -> dict[str, Any]:
        """Get Home Assistant configuration."""
        result: dict[str, Any] = await self.get("config")
        return result

    async def get_states(self) -> list[EntityState]:
        """Get all entity states."""
        data = await self.get("states")
        return [EntityState.from_dict(s) for s in data]

    async def get_state(self, entity_id: str) -> EntityState:
        """Get state of a specific entity."""
        data = await self.get(f"states/{entity_id}")
        return EntityState.from_dict(data)

    async def get_services(self) -> dict[str, list[Service]]:
        """Get all available services."""
        data = await self.get("services")
        result: dict[str, list[Service]] = {}
        for domain_data in data:
            domain = domain_data["domain"]
            services = []
            for service_name, service_data in domain_data.get("services", {}).items():
                services.append(Service.from_dict(domain, service_name, service_data))
            result[domain] = services
        return result

    async def call_service(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any] | None = None,
        target: dict[str, Any] | None = None,
    ) -> list[EntityState]:
        """Call a Home Assistant service."""
        data: dict[str, Any] = {}
        if service_data:
            data.update(service_data)
        if target:
            # Merge target directly into data (entity_id, device_id, area_id)
            data.update(target)

        logger.info("Calling service: %s.%s with data: %s", domain, service, data)
        result = await self.post(f"services/{domain}/{service}", data)

        if isinstance(result, list):
            return [EntityState.from_dict(s) for s in result]
        return []

    async def get_error_log(self) -> str:
        """Get the Home Assistant error log."""
        result: str = await self.get("error_log")
        return result

    async def get_logbook(
        self,
        entity_id: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get logbook entries."""
        endpoint = "logbook"
        if start_time:
            endpoint += f"/{start_time}"
        params = []
        if entity_id:
            params.append(f"entity={entity_id}")
        if end_time:
            params.append(f"end_time={end_time}")
        if params:
            endpoint += "?" + "&".join(params)

        result: list[dict[str, Any]] = await self.get(endpoint)
        return result

    async def get_history(
        self,
        entity_ids: list[str],
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[list[EntityState]]:
        """Get entity history."""
        endpoint = "history/period"
        if start_time:
            endpoint += f"/{start_time}"
        params = [f"filter_entity_id={','.join(entity_ids)}"]
        if end_time:
            params.append(f"end_time={end_time}")
        endpoint += "?" + "&".join(params)

        data = await self.get(endpoint)
        return [[EntityState.from_dict(s) for s in entity_history] for entity_history in data]

    async def send_telegram_message(
        self,
        message: str,
        chat_id: int | None = None,
        target: str | None = None,
    ) -> None:
        """Send a Telegram message via HA's telegram_bot service."""
        service_data: dict[str, Any] = {"message": message}
        if chat_id:
            service_data["target"] = chat_id
        elif target:
            service_data["target"] = target

        await self.call_service("telegram_bot", "send_message", service_data)

    # Automation CRUD operations

    async def get_automation_config(self, automation_id: str) -> dict[str, Any]:
        """Get the configuration of an automation.

        Args:
            automation_id: The automation ID (without 'automation.' prefix).

        Returns:
            The automation configuration dict.
        """
        # Remove 'automation.' prefix if present
        if automation_id.startswith("automation."):
            automation_id = automation_id[11:]

        result: dict[str, Any] = await self.get(f"config/automation/config/{automation_id}")
        return result

    async def create_automation(
        self,
        automation_id: str,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Create or update an automation.

        Args:
            automation_id: The automation ID (without 'automation.' prefix).
            config: The automation configuration (alias, trigger, action, etc.).

        Returns:
            The result of the operation.
        """
        # Remove 'automation.' prefix if present
        if automation_id.startswith("automation."):
            automation_id = automation_id[11:]

        logger.info("Creating/updating automation: %s", automation_id)
        result: dict[str, Any] = await self.post(
            f"config/automation/config/{automation_id}",
            config,
        )
        return result

    async def delete_automation(self, automation_id: str) -> dict[str, Any]:
        """Delete an automation.

        Args:
            automation_id: The automation ID (without 'automation.' prefix).

        Returns:
            The result of the operation.
        """
        # Remove 'automation.' prefix if present
        if automation_id.startswith("automation."):
            automation_id = automation_id[11:]

        logger.info("Deleting automation: %s", automation_id)
        result: dict[str, Any] = await self.delete(f"config/automation/config/{automation_id}")
        return result

    # Script CRUD operations

    async def get_script_config(self, script_id: str) -> dict[str, Any]:
        """Get the configuration of a script.

        Args:
            script_id: The script ID (without 'script.' prefix).

        Returns:
            The script configuration dict.
        """
        if script_id.startswith("script."):
            script_id = script_id[7:]

        result: dict[str, Any] = await self.get(f"config/script/config/{script_id}")
        return result

    async def create_script(
        self,
        script_id: str,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Create or update a script.

        Args:
            script_id: The script ID (without 'script.' prefix).
            config: The script configuration (alias, sequence, etc.).

        Returns:
            The result of the operation.
        """
        if script_id.startswith("script."):
            script_id = script_id[7:]

        logger.info("Creating/updating script: %s", script_id)
        result: dict[str, Any] = await self.post(
            f"config/script/config/{script_id}",
            config,
        )
        return result

    async def delete_script(self, script_id: str) -> dict[str, Any]:
        """Delete a script.

        Args:
            script_id: The script ID (without 'script.' prefix).

        Returns:
            The result of the operation.
        """
        if script_id.startswith("script."):
            script_id = script_id[7:]

        logger.info("Deleting script: %s", script_id)
        result: dict[str, Any] = await self.delete(f"config/script/config/{script_id}")
        return result

    # Scene CRUD operations

    async def get_scene_config(self, scene_id: str) -> dict[str, Any]:
        """Get the configuration of a scene.

        Args:
            scene_id: The scene ID (without 'scene.' prefix).

        Returns:
            The scene configuration dict.
        """
        if scene_id.startswith("scene."):
            scene_id = scene_id[6:]

        result: dict[str, Any] = await self.get(f"config/scene/config/{scene_id}")
        return result

    async def create_scene(
        self,
        scene_id: str,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Create or update a scene.

        Args:
            scene_id: The scene ID (without 'scene.' prefix).
            config: The scene configuration (name, entities, etc.).

        Returns:
            The result of the operation.
        """
        if scene_id.startswith("scene."):
            scene_id = scene_id[6:]

        logger.info("Creating/updating scene: %s", scene_id)
        result: dict[str, Any] = await self.post(
            f"config/scene/config/{scene_id}",
            config,
        )
        return result

    async def delete_scene(self, scene_id: str) -> dict[str, Any]:
        """Delete a scene.

        Args:
            scene_id: The scene ID (without 'scene.' prefix).

        Returns:
            The result of the operation.
        """
        if scene_id.startswith("scene."):
            scene_id = scene_id[6:]

        logger.info("Deleting scene: %s", scene_id)
        result: dict[str, Any] = await self.delete(f"config/scene/config/{scene_id}")
        return result

    # Helper CRUD operations (input_boolean, input_number, input_text, etc.)

    async def get_helper_config(self, helper_type: str, helper_id: str) -> dict[str, Any]:
        """Get the configuration of a helper.

        Args:
            helper_type: The helper type (input_boolean, input_number, etc.).
            helper_id: The helper ID (without the type prefix).

        Returns:
            The helper configuration dict.
        """
        prefix = f"{helper_type}."
        if helper_id.startswith(prefix):
            helper_id = helper_id[len(prefix) :]

        result: dict[str, Any] = await self.get(f"config/{helper_type}/config/{helper_id}")
        return result

    async def create_helper(
        self,
        helper_type: str,
        helper_id: str,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Create or update a helper.

        Args:
            helper_type: The helper type (input_boolean, input_number, etc.).
            helper_id: The helper ID (without the type prefix).
            config: The helper configuration.

        Returns:
            The result of the operation.
        """
        prefix = f"{helper_type}."
        if helper_id.startswith(prefix):
            helper_id = helper_id[len(prefix) :]

        logger.info("Creating/updating helper: %s.%s", helper_type, helper_id)
        result: dict[str, Any] = await self.post(
            f"config/{helper_type}/config/{helper_id}",
            config,
        )
        return result

    async def delete_helper(self, helper_type: str, helper_id: str) -> dict[str, Any]:
        """Delete a helper.

        Args:
            helper_type: The helper type (input_boolean, input_number, etc.).
            helper_id: The helper ID (without the type prefix).

        Returns:
            The result of the operation.
        """
        prefix = f"{helper_type}."
        if helper_id.startswith(prefix):
            helper_id = helper_id[len(prefix) :]

        logger.info("Deleting helper: %s.%s", helper_type, helper_id)
        result: dict[str, Any] = await self.delete(f"config/{helper_type}/config/{helper_id}")
        return result

    # Entity Registry operations (via WebSocket)

    async def _ws_command(self, command_type: str, **kwargs: Any) -> dict[str, Any] | None:
        """Send a WebSocket command and get the result.

        Entity registry operations require WebSocket, not REST API.

        Args:
            command_type: The command type.
            **kwargs: Command parameters.

        Returns:
            The result, or None if failed.
        """
        import json

        # Determine WebSocket URL based on REST URL
        if "supervisor" in self._base_url:
            ws_url = "ws://supervisor/core/websocket"
        elif "homeassistant" in self._base_url:
            ws_url = "ws://homeassistant:8123/api/websocket"
        else:
            # Convert http(s) REST URL to ws(s) WebSocket URL
            ws_url = self._base_url.replace("/api", "/api/websocket")
            ws_url = ws_url.replace("http://", "ws://").replace("https://", "wss://")

        session = await self._ensure_session()

        try:
            async with session.ws_connect(ws_url) as ws:
                # Wait for auth_required
                msg = await ws.receive()
                if msg.type != aiohttp.WSMsgType.TEXT:
                    raise HomeAssistantAPIError(0, f"Unexpected message type: {msg.type}")

                data = json.loads(msg.data)
                if data.get("type") != "auth_required":
                    raise HomeAssistantAPIError(0, f"Expected auth_required: {data}")

                # Authenticate
                await ws.send_json({"type": "auth", "access_token": self._token})

                msg = await ws.receive()
                data = json.loads(msg.data)
                if data.get("type") != "auth_ok":
                    raise HomeAssistantAPIError(401, "WebSocket authentication failed")

                # Send command
                command = {"id": 1, "type": command_type, **kwargs}
                await ws.send_json(command)

                # Wait for result
                msg = await ws.receive()
                data = json.loads(msg.data)

                if data.get("success"):
                    result: dict[str, Any] | None = data.get("result")
                    return result
                else:
                    error = data.get("error", {})
                    raise HomeAssistantAPIError(
                        0, f"WebSocket command failed: {error.get('message', 'Unknown error')}"
                    )

        except aiohttp.ClientError as e:
            raise HomeAssistantAPIError(0, f"WebSocket error: {e}") from e

    async def get_entity_registry(self) -> list[dict[str, Any]]:
        """Get all entities from the entity registry.

        Returns:
            List of entity registry entries.
        """
        result = await self._ws_command("config/entity_registry/list")
        if result is None:
            return []
        return result if isinstance(result, list) else []

    async def get_entity_registry_entry(self, entity_id: str) -> dict[str, Any] | None:
        """Get a specific entity's registry entry.

        Args:
            entity_id: The entity ID.

        Returns:
            Entity registry entry, or None if not found.
        """
        result = await self._ws_command("config/entity_registry/get", entity_id=entity_id)
        return result

    async def update_entity_registry(
        self,
        entity_id: str,
        name: str | None = None,
        area_id: str | None = None,
        labels: list[str] | None = None,
        disabled_by: str | None = None,
        hidden_by: str | None = None,
        icon: str | None = None,
    ) -> dict[str, Any]:
        """Update an entity's registry entry.

        Args:
            entity_id: The entity ID.
            name: New friendly name (None to leave unchanged).
            area_id: Area to assign to (None to leave unchanged, "" to clear).
            labels: Labels to assign (None to leave unchanged).
            disabled_by: Set to "user" to disable, None to enable.
            hidden_by: Set to "user" to hide, None to show.
            icon: Custom icon (None to leave unchanged).

        Returns:
            Updated entity registry entry.
        """
        kwargs: dict[str, Any] = {"entity_id": entity_id}

        if name is not None:
            kwargs["name"] = name
        if area_id is not None:
            kwargs["area_id"] = area_id if area_id else None
        if labels is not None:
            kwargs["labels"] = labels
        if disabled_by is not None:
            kwargs["disabled_by"] = disabled_by
        if hidden_by is not None:
            kwargs["hidden_by"] = hidden_by
        if icon is not None:
            kwargs["icon"] = icon

        logger.info("Updating entity registry: %s", entity_id)
        result = await self._ws_command("config/entity_registry/update", **kwargs)
        if result is None:
            raise HomeAssistantAPIError(0, f"Failed to update entity: {entity_id}")
        return result

    async def get_areas(self) -> list[dict[str, Any]]:
        """Get all areas.

        Returns:
            List of area registry entries.
        """
        result = await self._ws_command("config/area_registry/list")
        if result is None:
            return []
        return result if isinstance(result, list) else []

    async def get_labels(self) -> list[dict[str, Any]]:
        """Get all labels.

        Returns:
            List of label registry entries.
        """
        result = await self._ws_command("config/label_registry/list")
        if result is None:
            return []
        return result if isinstance(result, list) else []

    async def close(self) -> None:
        """Close the API session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
