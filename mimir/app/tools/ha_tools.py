"""Home Assistant tools for Mímir.

These tools allow the LLM to interact with Home Assistant,
querying states, calling services, and managing automations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import yaml

from ..utils.logging import get_logger
from .base import BaseTool

if TYPE_CHECKING:
    from ..ha.api import HomeAssistantAPI

logger = get_logger(__name__)


class GetEntitiesTool(BaseTool):
    """Tool to list entities in Home Assistant."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "get_entities"

    @property
    def description(self) -> str:
        return (
            "List entities in Home Assistant. Can filter by domain (e.g., 'light', 'automation', 'switch'). "
            "Returns entity IDs, states, and friendly names."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Filter by domain (e.g., 'light', 'automation', 'switch', 'sensor'). Leave empty for all entities.",
                },
                "search": {
                    "type": "string",
                    "description": "Search term to filter entity IDs or friendly names.",
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs: Any) -> str:
        domain = kwargs.get("domain", "").lower()
        search = kwargs.get("search", "").lower()

        try:
            states = await self._ha_api.get_states()

            # Filter by domain
            if domain:
                states = [s for s in states if s.entity_id.startswith(f"{domain}.")]

            # Filter by search term
            if search:
                states = [
                    s
                    for s in states
                    if search in s.entity_id.lower()
                    or search in (s.attributes.get("friendly_name", "") or "").lower()
                ]

            if not states:
                return "No entities found matching the criteria."

            # Format results
            results = []
            for state in states[:50]:  # Limit to 50 entities
                friendly_name = state.attributes.get("friendly_name", "")
                name_part = f" ({friendly_name})" if friendly_name else ""
                results.append(f"- {state.entity_id}{name_part}: {state.state}")

            output = f"Found {len(states)} entities"
            if len(states) > 50:
                output += " (showing first 50)"
            output += ":\n" + "\n".join(results)

            return output

        except Exception as e:
            logger.exception("Failed to get entities: %s", e)
            return f"Error getting entities: {e}"


class GetEntityStateTool(BaseTool):
    """Tool to get the state of a specific entity."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "get_entity_state"

    @property
    def description(self) -> str:
        return (
            "Get the current state and attributes of a specific Home Assistant entity. "
            "Use this to check the detailed state of lights, sensors, automations, etc."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The entity ID (e.g., 'light.bedroom', 'automation.motion_lights').",
                },
            },
            "required": ["entity_id"],
        }

    async def execute(self, **kwargs: Any) -> str:
        entity_id = kwargs.get("entity_id", "")

        if not entity_id:
            return "Error: entity_id is required."

        try:
            state = await self._ha_api.get_state(entity_id)

            result = f"Entity: {state.entity_id}\n"
            result += f"State: {state.state}\n"
            result += f"Last Changed: {state.last_changed}\n"

            if state.attributes:
                result += "Attributes:\n"
                for key, value in state.attributes.items():
                    result += f"  {key}: {value}\n"

            return result

        except Exception as e:
            logger.exception("Failed to get entity state: %s", e)
            return f"Error getting entity state: {e}"


class CallServiceTool(BaseTool):
    """Tool to call a Home Assistant service."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "call_service"

    @property
    def description(self) -> str:
        return (
            "Call a Home Assistant service. Use this to control devices, trigger automations, etc. "
            "Examples: turn on lights, run scripts, enable/disable automations."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Service domain (e.g., 'light', 'automation', 'switch', 'script').",
                },
                "service": {
                    "type": "string",
                    "description": "Service name (e.g., 'turn_on', 'turn_off', 'toggle', 'trigger').",
                },
                "entity_id": {
                    "type": "string",
                    "description": "Target entity ID (e.g., 'light.bedroom').",
                },
                "service_data": {
                    "type": "object",
                    "description": "Additional service data (e.g., {'brightness': 255} for lights).",
                },
            },
            "required": ["domain", "service"],
        }

    async def execute(self, **kwargs: Any) -> str:
        domain = kwargs.get("domain", "")
        service = kwargs.get("service", "")
        entity_id = kwargs.get("entity_id")
        service_data = kwargs.get("service_data", {})

        if not domain or not service:
            return "Error: domain and service are required."

        try:
            # Build target if entity_id provided
            target = {"entity_id": entity_id} if entity_id else None

            result = await self._ha_api.call_service(
                domain=domain,
                service=service,
                service_data=service_data or None,
                target=target,
            )

            if result:
                states = [f"{s.entity_id}: {s.state}" for s in result]
                return (
                    f"Service {domain}.{service} called successfully. Affected entities:\n"
                    + "\n".join(states)
                )
            else:
                return f"Service {domain}.{service} called successfully."

        except Exception as e:
            logger.exception("Failed to call service: %s", e)
            return f"Error calling service: {e}"


class GetAutomationsTool(BaseTool):
    """Tool to list and get details about automations."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "get_automations"

    @property
    def description(self) -> str:
        return (
            "List all automations in Home Assistant with their current state (on/off) and last triggered time. "
            "Use this to see what automations exist and their status."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "Search term to filter automation names or IDs.",
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs: Any) -> str:
        search = kwargs.get("search", "").lower()

        try:
            states = await self._ha_api.get_states()

            # Filter to automations only
            automations = [s for s in states if s.entity_id.startswith("automation.")]

            # Filter by search term
            if search:
                automations = [
                    a
                    for a in automations
                    if search in a.entity_id.lower()
                    or search in (a.attributes.get("friendly_name", "") or "").lower()
                ]

            if not automations:
                return "No automations found matching the criteria."

            # Format results
            results = []
            for auto in automations:
                friendly_name = auto.attributes.get("friendly_name", auto.entity_id)
                last_triggered = auto.attributes.get("last_triggered", "Never")
                status = "ON" if auto.state == "on" else "OFF"
                results.append(f"- [{status}] {friendly_name} ({auto.entity_id})")
                results.append(f"    Last triggered: {last_triggered}")

            return f"Found {len(automations)} automations:\n" + "\n".join(results)

        except Exception as e:
            logger.exception("Failed to get automations: %s", e)
            return f"Error getting automations: {e}"


class GetErrorLogTool(BaseTool):
    """Tool to get the Home Assistant error log."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "get_error_log"

    @property
    def description(self) -> str:
        return (
            "Get the Home Assistant error log. Shows recent errors and warnings. "
            "Use this to diagnose issues and troubleshoot problems."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "lines": {
                    "type": "integer",
                    "description": "Number of lines to return (default 50, max 200).",
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs: Any) -> str:
        lines = min(kwargs.get("lines", 50), 200)

        try:
            log = await self._ha_api.get_error_log()

            # Get last N lines
            log_lines = log.strip().split("\n")
            if len(log_lines) > lines:
                log_lines = log_lines[-lines:]

            if not log_lines or (len(log_lines) == 1 and not log_lines[0]):
                return "No errors in log."

            return f"Error log (last {len(log_lines)} lines):\n" + "\n".join(log_lines)

        except Exception as e:
            logger.exception("Failed to get error log: %s", e)
            return f"Error getting error log: {e}"


class GetServicesTool(BaseTool):
    """Tool to list available services in a domain."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "get_services"

    @property
    def description(self) -> str:
        return (
            "List available services for a domain. Shows what actions can be performed. "
            "Use this to discover what services are available for a specific integration."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Service domain to list (e.g., 'light', 'automation', 'switch'). Leave empty to list all domains.",
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs: Any) -> str:
        domain_filter = kwargs.get("domain", "").lower()

        try:
            services = await self._ha_api.get_services()

            if domain_filter:
                if domain_filter not in services:
                    return f"No services found for domain '{domain_filter}'."
                services = {domain_filter: services[domain_filter]}

            if not services:
                return "No services found."

            # Format results
            results = []
            for domain, domain_services in sorted(services.items()):
                if domain_filter or len(domain_services) <= 5:
                    # Show all services for specific domain or small domains
                    results.append(f"\n{domain}:")
                    for svc in domain_services:
                        desc = svc.description or ""
                        if len(desc) > 80:
                            desc = desc[:80] + "..."
                        results.append(f"  - {svc.name}: {desc}")
                else:
                    # Just show count for large domains
                    results.append(f"{domain}: {len(domain_services)} services")

            return "Available services:\n" + "\n".join(results)

        except Exception as e:
            logger.exception("Failed to get services: %s", e)
            return f"Error getting services: {e}"


class GetLogbookTool(BaseTool):
    """Tool to get logbook entries for entities."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "get_logbook"

    @property
    def description(self) -> str:
        return (
            "Get recent logbook entries showing what happened with entities. "
            "Use this to see the history of state changes and events."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Filter by entity ID (optional).",
                },
                "hours": {
                    "type": "integer",
                    "description": "How many hours of history to retrieve (default 24, max 168).",
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs: Any) -> str:
        entity_id = kwargs.get("entity_id")
        hours = min(kwargs.get("hours", 24), 168)

        try:
            from datetime import UTC, datetime, timedelta

            start_time = (datetime.now(UTC) - timedelta(hours=hours)).isoformat()

            entries = await self._ha_api.get_logbook(
                entity_id=entity_id,
                start_time=start_time,
            )

            if not entries:
                return "No logbook entries found for the specified criteria."

            # Limit results
            entries = entries[:50]

            # Format results
            results = []
            for entry in entries:
                when = entry.get("when", "")[:19]  # Trim microseconds
                name = entry.get("name", "Unknown")
                message = entry.get("message", entry.get("state", ""))
                results.append(f"[{when}] {name}: {message}")

            output = f"Logbook entries (last {hours} hours"
            if entity_id:
                output += f", entity: {entity_id}"
            output += "):\n" + "\n".join(results)

            if len(entries) == 50:
                output += "\n\n(Results limited to 50 entries)"

            return output

        except Exception as e:
            logger.exception("Failed to get logbook: %s", e)
            return f"Error getting logbook: {e}"


class GetAutomationConfigTool(BaseTool):
    """Tool to get the full configuration of an automation."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "get_automation_config"

    @property
    def description(self) -> str:
        return (
            "Get the full YAML configuration of an automation. "
            "Use this to see the triggers, conditions, and actions of an automation before modifying it."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The automation entity ID (e.g., 'automation.motion_lights').",
                },
            },
            "required": ["entity_id"],
        }

    async def execute(self, **kwargs: Any) -> str:
        entity_id = kwargs.get("entity_id", "")

        if not entity_id:
            return "Error: entity_id is required."

        # Ensure full entity_id format
        if not entity_id.startswith("automation."):
            entity_id = f"automation.{entity_id}"

        try:
            # First get the entity state to find the internal 'id' attribute
            state = await self._ha_api.get_state(entity_id)
            internal_id = state.attributes.get("id")

            if not internal_id:
                return (
                    f"Error: Automation '{entity_id}' does not have an internal ID. "
                    "This usually means it was created via YAML files instead of the UI. "
                    "Only UI-created automations can be retrieved through this API."
                )

            # Now get the config using the internal ID
            config = await self._ha_api.get_automation_config(internal_id)

            # Format as YAML for readability
            yaml_output = yaml.dump(
                config, default_flow_style=False, allow_unicode=True, sort_keys=False
            )

            return f"Automation configuration for '{entity_id}' (internal ID: {internal_id}):\n\n```yaml\n{yaml_output}```"

        except Exception as e:
            logger.exception("Failed to get automation config: %s", e)
            return f"Error getting automation config: {e}"


class CreateAutomationTool(BaseTool):
    """Tool to create a new automation."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "create_automation"

    @property
    def description(self) -> str:
        return (
            "Create a new automation in Home Assistant. "
            "Provide the automation ID and full configuration including alias, triggers, conditions, and actions. "
            "The configuration should follow Home Assistant automation YAML format."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "automation_id": {
                    "type": "string",
                    "description": "Unique ID for the automation (lowercase, underscores, e.g., 'bedroom_motion_light').",
                },
                "alias": {
                    "type": "string",
                    "description": "Human-readable name for the automation.",
                },
                "description": {
                    "type": "string",
                    "description": "Description of what the automation does.",
                },
                "trigger": {
                    "type": "array",
                    "description": "List of triggers (e.g., [{'platform': 'state', 'entity_id': 'binary_sensor.motion'}]).",
                },
                "condition": {
                    "type": "array",
                    "description": "List of conditions (optional).",
                },
                "action": {
                    "type": "array",
                    "description": "List of actions (e.g., [{'service': 'light.turn_on', 'target': {'entity_id': 'light.bedroom'}}]).",
                },
                "mode": {
                    "type": "string",
                    "description": "Automation mode: 'single', 'restart', 'queued', or 'parallel'. Default is 'single'.",
                },
            },
            "required": ["automation_id", "alias", "trigger", "action"],
        }

    async def execute(self, **kwargs: Any) -> str:
        automation_id = kwargs.get("automation_id", "")
        alias = kwargs.get("alias", "")
        description = kwargs.get("description", "")
        trigger = kwargs.get("trigger", [])
        condition = kwargs.get("condition", [])
        action = kwargs.get("action", [])
        mode = kwargs.get("mode", "single")

        if not automation_id or not alias or not trigger or not action:
            return "Error: automation_id, alias, trigger, and action are required."

        try:
            config: dict[str, Any] = {
                "alias": alias,
                "trigger": trigger,
                "action": action,
                "mode": mode,
            }

            if description:
                config["description"] = description

            if condition:
                config["condition"] = condition

            await self._ha_api.create_automation(automation_id, config)

            # Reload automations to apply changes
            await self._ha_api.call_service("automation", "reload")

            yaml_output = yaml.dump(
                config, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
            return f"Automation '{alias}' (automation.{automation_id}) created successfully!\n\n```yaml\n{yaml_output}```"

        except Exception as e:
            logger.exception("Failed to create automation: %s", e)
            return f"Error creating automation: {e}"


class UpdateAutomationTool(BaseTool):
    """Tool to update an existing automation."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "update_automation"

    @property
    def description(self) -> str:
        return (
            "Update an existing automation. First use get_automation_config to see the current config, "
            "then provide the full updated configuration. This will overwrite the existing automation."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The automation entity ID to update (e.g., 'automation.motion_lights').",
                },
                "config": {
                    "type": "object",
                    "description": "Full automation configuration (alias, trigger, condition, action, mode).",
                },
            },
            "required": ["entity_id", "config"],
        }

    async def execute(self, **kwargs: Any) -> str:
        entity_id = kwargs.get("entity_id", "")
        config = kwargs.get("config", {})

        if not entity_id or not config:
            return "Error: entity_id and config are required."

        # Ensure full entity_id format
        if not entity_id.startswith("automation."):
            entity_id = f"automation.{entity_id}"

        if "alias" not in config or "trigger" not in config or "action" not in config:
            return "Error: config must include at least 'alias', 'trigger', and 'action'."

        try:
            # First get the entity state to find the internal 'id' attribute
            state = await self._ha_api.get_state(entity_id)
            internal_id = state.attributes.get("id")

            if not internal_id:
                return (
                    f"Error: Automation '{entity_id}' does not have an internal ID. "
                    "This usually means it was created via YAML files instead of the UI. "
                    "Only UI-created automations can be updated through this API."
                )

            # Update using the internal ID
            await self._ha_api.create_automation(internal_id, config)

            # Reload automations to apply changes
            await self._ha_api.call_service("automation", "reload")

            yaml_output = yaml.dump(
                config, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
            return f"Automation '{entity_id}' updated successfully!\n\n```yaml\n{yaml_output}```"

        except Exception as e:
            logger.exception("Failed to update automation: %s", e)
            return f"Error updating automation: {e}"


class DeleteAutomationTool(BaseTool):
    """Tool to delete an automation."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "delete_automation"

    @property
    def description(self) -> str:
        return (
            "Delete an automation from Home Assistant. "
            "This permanently removes the automation. Use with caution."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The automation entity ID to delete (e.g., 'automation.motion_lights').",
                },
            },
            "required": ["entity_id"],
        }

    async def execute(self, **kwargs: Any) -> str:
        entity_id = kwargs.get("entity_id", "")

        if not entity_id:
            return "Error: entity_id is required."

        # Ensure full entity_id format
        if not entity_id.startswith("automation."):
            entity_id = f"automation.{entity_id}"

        try:
            # First get the entity state to find the internal 'id' attribute
            state = await self._ha_api.get_state(entity_id)
            internal_id = state.attributes.get("id")

            if not internal_id:
                return (
                    f"Error: Automation '{entity_id}' does not have an internal ID. "
                    "This usually means it was created via YAML files instead of the UI. "
                    "Only UI-created automations can be deleted through this API."
                )

            # Delete using the internal ID
            await self._ha_api.delete_automation(internal_id)

            # Reload automations to apply changes
            await self._ha_api.call_service("automation", "reload")

            return f"Automation '{entity_id}' deleted successfully."

        except Exception as e:
            logger.exception("Failed to delete automation: %s", e)
            return f"Error deleting automation: {e}"


# =============================================================================
# Script Tools
# =============================================================================


class GetScriptsTool(BaseTool):
    """Tool to list and get details about scripts."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "get_scripts"

    @property
    def description(self) -> str:
        return (
            "List all scripts in Home Assistant with their current state and last run time. "
            "Use this to see what scripts exist and their status."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "Search term to filter script names or IDs.",
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs: Any) -> str:
        search = kwargs.get("search", "").lower()

        try:
            states = await self._ha_api.get_states()

            # Filter to scripts only
            scripts = [s for s in states if s.entity_id.startswith("script.")]

            # Filter by search term
            if search:
                scripts = [
                    s
                    for s in scripts
                    if search in s.entity_id.lower()
                    or search in (s.attributes.get("friendly_name", "") or "").lower()
                ]

            if not scripts:
                return "No scripts found matching the criteria."

            # Format results
            results = []
            for script in scripts:
                friendly_name = script.attributes.get("friendly_name", script.entity_id)
                last_triggered = script.attributes.get("last_triggered", "Never")
                mode = script.attributes.get("mode", "single")
                results.append(f"- {friendly_name} ({script.entity_id})")
                results.append(f"    Mode: {mode}, Last run: {last_triggered}")

            return f"Found {len(scripts)} scripts:\n" + "\n".join(results)

        except Exception as e:
            logger.exception("Failed to get scripts: %s", e)
            return f"Error getting scripts: {e}"


class GetScriptConfigTool(BaseTool):
    """Tool to get the full configuration of a script."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "get_script_config"

    @property
    def description(self) -> str:
        return (
            "Get the full YAML configuration of a script. "
            "Use this to see the sequence of actions before modifying it."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The script entity ID (e.g., 'script.morning_routine').",
                },
            },
            "required": ["entity_id"],
        }

    async def execute(self, **kwargs: Any) -> str:
        entity_id = kwargs.get("entity_id", "")

        if not entity_id:
            return "Error: entity_id is required."

        if not entity_id.startswith("script."):
            entity_id = f"script.{entity_id}"

        try:
            state = await self._ha_api.get_state(entity_id)
            internal_id = state.attributes.get("id")

            if not internal_id:
                # For scripts, we use the entity_id suffix as the ID
                internal_id = entity_id[7:]  # Remove 'script.'

            config = await self._ha_api.get_script_config(internal_id)

            yaml_output = yaml.dump(
                config, default_flow_style=False, allow_unicode=True, sort_keys=False
            )

            return f"Script configuration for '{entity_id}':\n\n```yaml\n{yaml_output}```"

        except Exception as e:
            logger.exception("Failed to get script config: %s", e)
            return f"Error getting script config: {e}"


class CreateScriptTool(BaseTool):
    """Tool to create a new script."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "create_script"

    @property
    def description(self) -> str:
        return (
            "Create a new script in Home Assistant. "
            "Provide the script ID and configuration including alias and sequence of actions."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "script_id": {
                    "type": "string",
                    "description": "Unique ID for the script (lowercase, underscores, e.g., 'morning_routine').",
                },
                "alias": {
                    "type": "string",
                    "description": "Human-readable name for the script.",
                },
                "description": {
                    "type": "string",
                    "description": "Description of what the script does.",
                },
                "sequence": {
                    "type": "array",
                    "description": "List of actions to perform (e.g., [{'service': 'light.turn_on', 'target': {'entity_id': 'light.bedroom'}}]).",
                },
                "mode": {
                    "type": "string",
                    "description": "Script mode: 'single', 'restart', 'queued', or 'parallel'. Default is 'single'.",
                },
                "icon": {
                    "type": "string",
                    "description": "Icon for the script (e.g., 'mdi:script').",
                },
            },
            "required": ["script_id", "alias", "sequence"],
        }

    async def execute(self, **kwargs: Any) -> str:
        script_id = kwargs.get("script_id", "")
        alias = kwargs.get("alias", "")
        description = kwargs.get("description", "")
        sequence = kwargs.get("sequence", [])
        mode = kwargs.get("mode", "single")
        icon = kwargs.get("icon", "")

        if not script_id or not alias or not sequence:
            return "Error: script_id, alias, and sequence are required."

        try:
            config: dict[str, Any] = {
                "alias": alias,
                "sequence": sequence,
                "mode": mode,
            }

            if description:
                config["description"] = description
            if icon:
                config["icon"] = icon

            await self._ha_api.create_script(script_id, config)

            # Reload scripts to apply changes
            await self._ha_api.call_service("script", "reload")

            yaml_output = yaml.dump(
                config, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
            return f"Script '{alias}' (script.{script_id}) created successfully!\n\n```yaml\n{yaml_output}```"

        except Exception as e:
            logger.exception("Failed to create script: %s", e)
            return f"Error creating script: {e}"


class UpdateScriptTool(BaseTool):
    """Tool to update an existing script."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "update_script"

    @property
    def description(self) -> str:
        return (
            "Update an existing script. First use get_script_config to see the current config, "
            "then provide the full updated configuration."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The script entity ID to update (e.g., 'script.morning_routine').",
                },
                "config": {
                    "type": "object",
                    "description": "Full script configuration (alias, sequence, mode, etc.).",
                },
            },
            "required": ["entity_id", "config"],
        }

    async def execute(self, **kwargs: Any) -> str:
        entity_id = kwargs.get("entity_id", "")
        config = kwargs.get("config", {})

        if not entity_id or not config:
            return "Error: entity_id and config are required."

        if not entity_id.startswith("script."):
            entity_id = f"script.{entity_id}"

        if "alias" not in config or "sequence" not in config:
            return "Error: config must include at least 'alias' and 'sequence'."

        try:
            script_id = entity_id[7:]  # Remove 'script.'
            await self._ha_api.create_script(script_id, config)

            # Reload scripts to apply changes
            await self._ha_api.call_service("script", "reload")

            yaml_output = yaml.dump(
                config, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
            return f"Script '{entity_id}' updated successfully!\n\n```yaml\n{yaml_output}```"

        except Exception as e:
            logger.exception("Failed to update script: %s", e)
            return f"Error updating script: {e}"


class DeleteScriptTool(BaseTool):
    """Tool to delete a script."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "delete_script"

    @property
    def description(self) -> str:
        return (
            "Delete a script from Home Assistant. "
            "This permanently removes the script. Use with caution."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The script entity ID to delete (e.g., 'script.morning_routine').",
                },
            },
            "required": ["entity_id"],
        }

    async def execute(self, **kwargs: Any) -> str:
        entity_id = kwargs.get("entity_id", "")

        if not entity_id:
            return "Error: entity_id is required."

        if not entity_id.startswith("script."):
            entity_id = f"script.{entity_id}"

        try:
            script_id = entity_id[7:]  # Remove 'script.'
            await self._ha_api.delete_script(script_id)

            # Reload scripts to apply changes
            await self._ha_api.call_service("script", "reload")

            return f"Script '{entity_id}' deleted successfully."

        except Exception as e:
            logger.exception("Failed to delete script: %s", e)
            return f"Error deleting script: {e}"


# =============================================================================
# Scene Tools
# =============================================================================


class GetScenesTool(BaseTool):
    """Tool to list and get details about scenes."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "get_scenes"

    @property
    def description(self) -> str:
        return (
            "List all scenes in Home Assistant. "
            "Use this to see what scenes exist and their configuration."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "Search term to filter scene names or IDs.",
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs: Any) -> str:
        search = kwargs.get("search", "").lower()

        try:
            states = await self._ha_api.get_states()

            # Filter to scenes only
            scenes = [s for s in states if s.entity_id.startswith("scene.")]

            # Filter by search term
            if search:
                scenes = [
                    s
                    for s in scenes
                    if search in s.entity_id.lower()
                    or search in (s.attributes.get("friendly_name", "") or "").lower()
                ]

            if not scenes:
                return "No scenes found matching the criteria."

            # Format results
            results = []
            for scene in scenes:
                friendly_name = scene.attributes.get("friendly_name", scene.entity_id)
                entity_ids = scene.attributes.get("entity_id", [])
                entity_count = len(entity_ids) if isinstance(entity_ids, list) else 0
                results.append(f"- {friendly_name} ({scene.entity_id}) - {entity_count} entities")

            return f"Found {len(scenes)} scenes:\n" + "\n".join(results)

        except Exception as e:
            logger.exception("Failed to get scenes: %s", e)
            return f"Error getting scenes: {e}"


class GetSceneConfigTool(BaseTool):
    """Tool to get the full configuration of a scene."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "get_scene_config"

    @property
    def description(self) -> str:
        return (
            "Get the full configuration of a scene including all entity states. "
            "Use this to see what entities and states are included in the scene."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The scene entity ID (e.g., 'scene.movie_night').",
                },
            },
            "required": ["entity_id"],
        }

    async def execute(self, **kwargs: Any) -> str:
        entity_id = kwargs.get("entity_id", "")

        if not entity_id:
            return "Error: entity_id is required."

        if not entity_id.startswith("scene."):
            entity_id = f"scene.{entity_id}"

        try:
            state = await self._ha_api.get_state(entity_id)
            internal_id = state.attributes.get("id")

            if not internal_id:
                internal_id = entity_id[6:]  # Remove 'scene.'

            config = await self._ha_api.get_scene_config(internal_id)

            yaml_output = yaml.dump(
                config, default_flow_style=False, allow_unicode=True, sort_keys=False
            )

            return f"Scene configuration for '{entity_id}':\n\n```yaml\n{yaml_output}```"

        except Exception as e:
            logger.exception("Failed to get scene config: %s", e)
            return f"Error getting scene config: {e}"


class CreateSceneTool(BaseTool):
    """Tool to create a new scene."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "create_scene"

    @property
    def description(self) -> str:
        return (
            "Create a new scene in Home Assistant. "
            "Provide entity states that should be applied when the scene is activated."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "scene_id": {
                    "type": "string",
                    "description": "Unique ID for the scene (lowercase, underscores, e.g., 'movie_night').",
                },
                "name": {
                    "type": "string",
                    "description": "Human-readable name for the scene.",
                },
                "entities": {
                    "type": "object",
                    "description": "Entity states to set (e.g., {'light.living_room': {'state': 'on', 'brightness': 50}}).",
                },
                "icon": {
                    "type": "string",
                    "description": "Icon for the scene (e.g., 'mdi:movie').",
                },
            },
            "required": ["scene_id", "name", "entities"],
        }

    async def execute(self, **kwargs: Any) -> str:
        scene_id = kwargs.get("scene_id", "")
        name = kwargs.get("name", "")
        entities = kwargs.get("entities", {})
        icon = kwargs.get("icon", "")

        if not scene_id or not name or not entities:
            return "Error: scene_id, name, and entities are required."

        try:
            config: dict[str, Any] = {
                "name": name,
                "entities": entities,
            }

            if icon:
                config["icon"] = icon

            await self._ha_api.create_scene(scene_id, config)

            # Reload scenes to apply changes
            await self._ha_api.call_service("scene", "reload")

            yaml_output = yaml.dump(
                config, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
            return f"Scene '{name}' (scene.{scene_id}) created successfully!\n\n```yaml\n{yaml_output}```"

        except Exception as e:
            logger.exception("Failed to create scene: %s", e)
            return f"Error creating scene: {e}"


class UpdateSceneTool(BaseTool):
    """Tool to update an existing scene."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "update_scene"

    @property
    def description(self) -> str:
        return (
            "Update an existing scene. First use get_scene_config to see the current config, "
            "then provide the full updated configuration."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The scene entity ID to update (e.g., 'scene.movie_night').",
                },
                "config": {
                    "type": "object",
                    "description": "Full scene configuration (name, entities, icon).",
                },
            },
            "required": ["entity_id", "config"],
        }

    async def execute(self, **kwargs: Any) -> str:
        entity_id = kwargs.get("entity_id", "")
        config = kwargs.get("config", {})

        if not entity_id or not config:
            return "Error: entity_id and config are required."

        if not entity_id.startswith("scene."):
            entity_id = f"scene.{entity_id}"

        if "name" not in config or "entities" not in config:
            return "Error: config must include at least 'name' and 'entities'."

        try:
            scene_id = entity_id[6:]  # Remove 'scene.'
            await self._ha_api.create_scene(scene_id, config)

            # Reload scenes to apply changes
            await self._ha_api.call_service("scene", "reload")

            yaml_output = yaml.dump(
                config, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
            return f"Scene '{entity_id}' updated successfully!\n\n```yaml\n{yaml_output}```"

        except Exception as e:
            logger.exception("Failed to update scene: %s", e)
            return f"Error updating scene: {e}"


class DeleteSceneTool(BaseTool):
    """Tool to delete a scene."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "delete_scene"

    @property
    def description(self) -> str:
        return (
            "Delete a scene from Home Assistant. "
            "This permanently removes the scene. Use with caution."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The scene entity ID to delete (e.g., 'scene.movie_night').",
                },
            },
            "required": ["entity_id"],
        }

    async def execute(self, **kwargs: Any) -> str:
        entity_id = kwargs.get("entity_id", "")

        if not entity_id:
            return "Error: entity_id is required."

        if not entity_id.startswith("scene."):
            entity_id = f"scene.{entity_id}"

        try:
            scene_id = entity_id[6:]  # Remove 'scene.'
            await self._ha_api.delete_scene(scene_id)

            # Reload scenes to apply changes
            await self._ha_api.call_service("scene", "reload")

            return f"Scene '{entity_id}' deleted successfully."

        except Exception as e:
            logger.exception("Failed to delete scene: %s", e)
            return f"Error deleting scene: {e}"


# =============================================================================
# Helper Tools
# =============================================================================


class GetHelpersTool(BaseTool):
    """Tool to list and get details about input helpers."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "get_helpers"

    @property
    def description(self) -> str:
        return (
            "List all input helpers in Home Assistant (input_boolean, input_number, "
            "input_text, input_select, input_datetime, counter, timer). "
            "Use this to see what helpers exist and their current values."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "helper_type": {
                    "type": "string",
                    "description": "Filter by type: input_boolean, input_number, input_text, input_select, input_datetime, counter, timer. Leave empty for all.",
                },
                "search": {
                    "type": "string",
                    "description": "Search term to filter helper names or IDs.",
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs: Any) -> str:
        helper_type = kwargs.get("helper_type", "").lower()
        search = kwargs.get("search", "").lower()

        helper_domains = [
            "input_boolean",
            "input_number",
            "input_text",
            "input_select",
            "input_datetime",
            "counter",
            "timer",
        ]

        try:
            states = await self._ha_api.get_states()

            # Filter to helpers only
            if helper_type:
                if helper_type not in helper_domains:
                    return f"Error: Unknown helper type '{helper_type}'. Valid types: {', '.join(helper_domains)}"
                helpers = [s for s in states if s.entity_id.startswith(f"{helper_type}.")]
            else:
                helpers = [
                    s
                    for s in states
                    if any(s.entity_id.startswith(f"{d}.") for d in helper_domains)
                ]

            # Filter by search term
            if search:
                helpers = [
                    h
                    for h in helpers
                    if search in h.entity_id.lower()
                    or search in (h.attributes.get("friendly_name", "") or "").lower()
                ]

            if not helpers:
                return "No helpers found matching the criteria."

            # Format results grouped by type
            results_by_type: dict[str, list[str]] = {}
            for helper in helpers:
                domain = helper.entity_id.split(".")[0]
                friendly_name = helper.attributes.get("friendly_name", helper.entity_id)
                if domain not in results_by_type:
                    results_by_type[domain] = []
                results_by_type[domain].append(f"  - {friendly_name}: {helper.state}")

            results = []
            for domain, items in sorted(results_by_type.items()):
                results.append(f"\n{domain.upper().replace('_', ' ')}:")
                results.extend(items)

            return f"Found {len(helpers)} helpers:" + "\n".join(results)

        except Exception as e:
            logger.exception("Failed to get helpers: %s", e)
            return f"Error getting helpers: {e}"


class CreateHelperTool(BaseTool):
    """Tool to create a new input helper."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "create_helper"

    @property
    def description(self) -> str:
        return (
            "Create a new input helper (input_boolean, input_number, input_text, input_select). "
            "Helpers are useful for storing state or user preferences."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "helper_type": {
                    "type": "string",
                    "description": "Type of helper: input_boolean, input_number, input_text, input_select, counter.",
                },
                "helper_id": {
                    "type": "string",
                    "description": "Unique ID for the helper (lowercase, underscores, e.g., 'guest_mode').",
                },
                "name": {
                    "type": "string",
                    "description": "Human-readable name for the helper.",
                },
                "icon": {
                    "type": "string",
                    "description": "Icon for the helper (e.g., 'mdi:toggle-switch').",
                },
                "initial": {
                    "type": "string",
                    "description": "Initial value (for input_number/input_text/input_select).",
                },
                "min": {
                    "type": "number",
                    "description": "Minimum value (for input_number).",
                },
                "max": {
                    "type": "number",
                    "description": "Maximum value (for input_number).",
                },
                "step": {
                    "type": "number",
                    "description": "Step value (for input_number).",
                },
                "options": {
                    "type": "array",
                    "description": "List of options (for input_select).",
                },
            },
            "required": ["helper_type", "helper_id", "name"],
        }

    async def execute(self, **kwargs: Any) -> str:
        helper_type = kwargs.get("helper_type", "")
        helper_id = kwargs.get("helper_id", "")
        name = kwargs.get("name", "")

        valid_types = ["input_boolean", "input_number", "input_text", "input_select", "counter"]
        if helper_type not in valid_types:
            return f"Error: Invalid helper_type. Must be one of: {', '.join(valid_types)}"

        if not helper_id or not name:
            return "Error: helper_id and name are required."

        try:
            config: dict[str, Any] = {"name": name}

            if kwargs.get("icon"):
                config["icon"] = kwargs["icon"]

            # Type-specific options
            if helper_type == "input_number":
                config["min"] = kwargs.get("min", 0)
                config["max"] = kwargs.get("max", 100)
                if kwargs.get("step"):
                    config["step"] = kwargs["step"]
                if kwargs.get("initial"):
                    config["initial"] = float(kwargs["initial"])

            elif helper_type == "input_text":
                if kwargs.get("initial"):
                    config["initial"] = kwargs["initial"]

            elif helper_type == "input_select":
                options = kwargs.get("options", [])
                if not options:
                    return "Error: options are required for input_select."
                config["options"] = options
                if kwargs.get("initial"):
                    config["initial"] = kwargs["initial"]

            elif helper_type == "counter":
                if kwargs.get("initial"):
                    config["initial"] = int(kwargs["initial"])
                if kwargs.get("step"):
                    config["step"] = int(kwargs["step"])

            await self._ha_api.create_helper(helper_type, helper_id, config)

            # Reload the helper domain
            await self._ha_api.call_service(helper_type, "reload")

            yaml_output = yaml.dump(
                config, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
            return f"Helper '{name}' ({helper_type}.{helper_id}) created successfully!\n\n```yaml\n{yaml_output}```"

        except Exception as e:
            logger.exception("Failed to create helper: %s", e)
            return f"Error creating helper: {e}"


class DeleteHelperTool(BaseTool):
    """Tool to delete an input helper."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "delete_helper"

    @property
    def description(self) -> str:
        return (
            "Delete an input helper from Home Assistant. "
            "This permanently removes the helper. Use with caution."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The helper entity ID to delete (e.g., 'input_boolean.guest_mode').",
                },
            },
            "required": ["entity_id"],
        }

    async def execute(self, **kwargs: Any) -> str:
        entity_id = kwargs.get("entity_id", "")

        if not entity_id:
            return "Error: entity_id is required."

        valid_types = [
            "input_boolean",
            "input_number",
            "input_text",
            "input_select",
            "input_datetime",
            "counter",
            "timer",
        ]

        # Determine helper type from entity_id
        helper_type = None
        for t in valid_types:
            if entity_id.startswith(f"{t}."):
                helper_type = t
                break

        if not helper_type:
            return f"Error: entity_id must start with one of: {', '.join(valid_types)}"

        try:
            helper_id = entity_id[len(helper_type) + 1 :]  # Remove type prefix
            await self._ha_api.delete_helper(helper_type, helper_id)

            # Reload the helper domain
            await self._ha_api.call_service(helper_type, "reload")

            return f"Helper '{entity_id}' deleted successfully."

        except Exception as e:
            logger.exception("Failed to delete helper: %s", e)
            return f"Error deleting helper: {e}"


# =============================================================================
# Entity Registry Tools
# =============================================================================


class RenameEntityTool(BaseTool):
    """Tool to rename an entity's friendly name."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "rename_entity"

    @property
    def description(self) -> str:
        return (
            "Rename an entity by changing its friendly name in the entity registry. "
            "This changes how the entity appears in the UI and voice assistants."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The entity ID to rename (e.g., 'light.living_room').",
                },
                "new_name": {
                    "type": "string",
                    "description": "The new friendly name for the entity.",
                },
            },
            "required": ["entity_id", "new_name"],
        }

    async def execute(self, **kwargs: Any) -> str:
        entity_id = kwargs.get("entity_id", "")
        new_name = kwargs.get("new_name", "")

        if not entity_id or not new_name:
            return "Error: entity_id and new_name are required."

        try:
            await self._ha_api.update_entity_registry(
                entity_id=entity_id,
                name=new_name,
            )

            return f"Entity '{entity_id}' renamed to '{new_name}' successfully."

        except Exception as e:
            logger.exception("Failed to rename entity: %s", e)
            return f"Error renaming entity: {e}"


class AssignEntityAreaTool(BaseTool):
    """Tool to assign an entity to an area."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "assign_entity_area"

    @property
    def description(self) -> str:
        return (
            "Assign an entity to an area in Home Assistant. "
            "Areas help organize entities by room or location. "
            "Use get_entities to see available areas first."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The entity ID to assign (e.g., 'light.living_room').",
                },
                "area_id": {
                    "type": "string",
                    "description": "The area ID to assign to (e.g., 'living_room'). Use empty string to clear the area assignment.",
                },
            },
            "required": ["entity_id", "area_id"],
        }

    async def execute(self, **kwargs: Any) -> str:
        entity_id = kwargs.get("entity_id", "")
        area_id = kwargs.get("area_id", "")

        if not entity_id:
            return "Error: entity_id is required."

        try:
            # If area_id is empty string, we clear the area
            if area_id == "":
                await self._ha_api.update_entity_registry(
                    entity_id=entity_id,
                    area_id="",  # This clears the area
                )
                return f"Entity '{entity_id}' removed from its area."
            else:
                await self._ha_api.update_entity_registry(
                    entity_id=entity_id,
                    area_id=area_id,
                )
                return f"Entity '{entity_id}' assigned to area '{area_id}' successfully."

        except Exception as e:
            logger.exception("Failed to assign entity area: %s", e)
            return f"Error assigning entity area: {e}"


class AssignEntityLabelsTool(BaseTool):
    """Tool to assign labels to an entity."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "assign_entity_labels"

    @property
    def description(self) -> str:
        return (
            "Assign labels to an entity in Home Assistant. "
            "Labels are tags that help categorize and organize entities. "
            "Provide the full list of labels (previous labels will be replaced)."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The entity ID to assign labels to (e.g., 'light.living_room').",
                },
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of label IDs to assign. Use empty array to clear all labels.",
                },
            },
            "required": ["entity_id", "labels"],
        }

    async def execute(self, **kwargs: Any) -> str:
        entity_id = kwargs.get("entity_id", "")
        labels = kwargs.get("labels", [])

        if not entity_id:
            return "Error: entity_id is required."

        if not isinstance(labels, list):
            return "Error: labels must be a list of strings."

        try:
            await self._ha_api.update_entity_registry(
                entity_id=entity_id,
                labels=labels,
            )

            if labels:
                return f"Entity '{entity_id}' assigned labels: {', '.join(labels)}"
            else:
                return f"Entity '{entity_id}' labels cleared."

        except Exception as e:
            logger.exception("Failed to assign entity labels: %s", e)
            return f"Error assigning entity labels: {e}"


class GetAreasTool(BaseTool):
    """Tool to list all areas in Home Assistant."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "get_areas"

    @property
    def description(self) -> str:
        return (
            "List all areas defined in Home Assistant. "
            "Use this to see available areas before assigning entities to them."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self, **kwargs: Any) -> str:  # noqa: ARG002
        try:
            areas = await self._ha_api.get_areas()

            if not areas:
                return "No areas defined in Home Assistant."

            results = []
            for area in areas:
                name = area.get("name", "Unknown")
                area_id = area.get("area_id", "")
                icon = area.get("icon", "")
                icon_str = f" ({icon})" if icon else ""
                results.append(f"- {name}{icon_str} [id: {area_id}]")

            return f"Found {len(areas)} areas:\n" + "\n".join(results)

        except Exception as e:
            logger.exception("Failed to get areas: %s", e)
            return f"Error getting areas: {e}"


class GetLabelsTool(BaseTool):
    """Tool to list all labels in Home Assistant."""

    def __init__(self, ha_api: HomeAssistantAPI) -> None:
        self._ha_api = ha_api

    @property
    def name(self) -> str:
        return "get_labels"

    @property
    def description(self) -> str:
        return (
            "List all labels defined in Home Assistant. "
            "Use this to see available labels before assigning them to entities."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self, **kwargs: Any) -> str:  # noqa: ARG002
        try:
            labels = await self._ha_api.get_labels()

            if not labels:
                return "No labels defined in Home Assistant."

            results = []
            for label in labels:
                name = label.get("name", "Unknown")
                label_id = label.get("label_id", "")
                color = label.get("color", "")
                icon = label.get("icon", "")
                extras = []
                if color:
                    extras.append(f"color: {color}")
                if icon:
                    extras.append(f"icon: {icon}")
                extras_str = f" ({', '.join(extras)})" if extras else ""
                results.append(f"- {name}{extras_str} [id: {label_id}]")

            return f"Found {len(labels)} labels:\n" + "\n".join(results)

        except Exception as e:
            logger.exception("Failed to get labels: %s", e)
            return f"Error getting labels: {e}"
