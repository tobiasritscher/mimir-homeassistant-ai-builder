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
                    s for s in states
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
                return f"Service {domain}.{service} called successfully. Affected entities:\n" + "\n".join(states)
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
                    a for a in automations
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
                        desc = svc.description[:80] + "..." if len(svc.description) > 80 else svc.description
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
            yaml_output = yaml.dump(config, default_flow_style=False, allow_unicode=True, sort_keys=False)

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

            yaml_output = yaml.dump(config, default_flow_style=False, allow_unicode=True, sort_keys=False)
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

            yaml_output = yaml.dump(config, default_flow_style=False, allow_unicode=True, sort_keys=False)
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
