"""REST API client for Home Assistant."""

from __future__ import annotations

import os
from typing import Any

import aiohttp

from ..utils.logging import get_logger
from .types import Entity, EntityState, Service

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
            url: Home Assistant URL. If None, uses Supervisor proxy.
            token: Access token. If None, uses SUPERVISOR_TOKEN.
        """
        # Detect add-on environment
        supervisor_token = os.environ.get("SUPERVISOR_TOKEN")

        if supervisor_token and not url:
            # Running as add-on - use Supervisor proxy
            self._base_url = "http://supervisor/core/api"
            self._token = supervisor_token
            logger.info("Using Supervisor API proxy")
        else:
            # Standalone mode
            self._base_url = f"{url.rstrip('/')}/api" if url else "http://homeassistant.local:8123/api"
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
        return await self.get("config")

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
            data["target"] = target

        logger.info("Calling service: %s.%s", domain, service)
        result = await self.post(f"services/{domain}/{service}", data)

        if isinstance(result, list):
            return [EntityState.from_dict(s) for s in result]
        return []

    async def get_error_log(self) -> str:
        """Get the Home Assistant error log."""
        return await self.get("error_log")

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

        return await self.get(endpoint)

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

    async def close(self) -> None:
        """Close the API session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
