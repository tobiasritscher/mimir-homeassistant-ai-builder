"""Operating mode manager for Mímir.

Manages operating modes (Chat, Normal, YOLO) with YOLO timer support.
"""

from __future__ import annotations

import asyncio  # noqa: TC003
import time
from collections.abc import Callable  # noqa: TC003
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..utils.logging import get_logger

logger = get_logger(__name__)


class OperatingMode(str, Enum):
    """Agent operating modes."""

    CHAT = "chat"  # Read-only
    NORMAL = "normal"  # With confirmations
    YOLO = "yolo"  # Auto-approve all


class ToolCategory(str, Enum):
    """Categories of tools for mode enforcement."""

    READ_ONLY = "read_only"  # Always allowed
    WRITE = "write"  # Requires Normal or YOLO mode
    DESTRUCTIVE = "destructive"  # Delete operations


# Tool categorization for mode enforcement
TOOL_CATEGORIES: dict[str, ToolCategory] = {
    # Read-only tools (always allowed)
    "get_entities": ToolCategory.READ_ONLY,
    "get_entity_state": ToolCategory.READ_ONLY,
    "get_automations": ToolCategory.READ_ONLY,
    "get_automation_config": ToolCategory.READ_ONLY,
    "get_scripts": ToolCategory.READ_ONLY,
    "get_script_config": ToolCategory.READ_ONLY,
    "get_scenes": ToolCategory.READ_ONLY,
    "get_scene_config": ToolCategory.READ_ONLY,
    "get_helpers": ToolCategory.READ_ONLY,
    "get_services": ToolCategory.READ_ONLY,
    "get_error_log": ToolCategory.READ_ONLY,
    "get_logbook": ToolCategory.READ_ONLY,
    "recall_memories": ToolCategory.READ_ONLY,
    "web_search": ToolCategory.READ_ONLY,
    "ha_docs_search": ToolCategory.READ_ONLY,
    "hacs_search": ToolCategory.READ_ONLY,
    # Write tools (requires Normal or YOLO)
    "call_service": ToolCategory.WRITE,
    "create_automation": ToolCategory.WRITE,
    "update_automation": ToolCategory.WRITE,
    "create_script": ToolCategory.WRITE,
    "update_script": ToolCategory.WRITE,
    "create_scene": ToolCategory.WRITE,
    "update_scene": ToolCategory.WRITE,
    "create_helper": ToolCategory.WRITE,
    "store_memory": ToolCategory.WRITE,
    "rename_entity": ToolCategory.WRITE,
    "assign_entity_area": ToolCategory.WRITE,
    "assign_entity_labels": ToolCategory.WRITE,
    # Destructive tools (delete operations)
    "delete_automation": ToolCategory.DESTRUCTIVE,
    "delete_script": ToolCategory.DESTRUCTIVE,
    "delete_scene": ToolCategory.DESTRUCTIVE,
    "delete_helper": ToolCategory.DESTRUCTIVE,
    "forget_memory": ToolCategory.DESTRUCTIVE,
}


def get_tool_category(tool_name: str) -> ToolCategory:
    """Get the category of a tool.

    Args:
        tool_name: Name of the tool.

    Returns:
        Tool category, defaults to WRITE if unknown.
    """
    return TOOL_CATEGORIES.get(tool_name, ToolCategory.WRITE)


def is_write_operation(tool_name: str) -> bool:
    """Check if a tool is a write operation.

    Args:
        tool_name: Name of the tool.

    Returns:
        True if the tool modifies state.
    """
    category = get_tool_category(tool_name)
    return category in (ToolCategory.WRITE, ToolCategory.DESTRUCTIVE)


@dataclass
class ModeManager:
    """Manages operating modes and YOLO timer.

    Attributes:
        current_mode: Current operating mode.
        yolo_duration_minutes: How long YOLO mode lasts.
    """

    yolo_duration_minutes: int = 10
    _current_mode: OperatingMode = field(default=OperatingMode.NORMAL)
    _yolo_activated_at: float | None = field(default=None)
    _yolo_task: asyncio.Task[None] | None = field(default=None)
    _mode_change_callback: Callable[[OperatingMode], None] | None = field(default=None)

    @property
    def current_mode(self) -> OperatingMode:
        """Get the current operating mode, checking YOLO expiry."""
        if self._current_mode == OperatingMode.YOLO and self._is_yolo_expired():
            logger.info("YOLO mode has expired, reverting to Normal mode")
            self._current_mode = OperatingMode.NORMAL
            self._yolo_activated_at = None
            if self._mode_change_callback:
                self._mode_change_callback(OperatingMode.NORMAL)
        return self._current_mode

    @property
    def yolo_remaining_seconds(self) -> int:
        """Get remaining seconds of YOLO mode, or 0 if not in YOLO mode."""
        if self._current_mode != OperatingMode.YOLO or not self._yolo_activated_at:
            return 0
        elapsed = time.time() - self._yolo_activated_at
        remaining = (self.yolo_duration_minutes * 60) - elapsed
        return max(0, int(remaining))

    @property
    def yolo_remaining_minutes(self) -> float:
        """Get remaining minutes of YOLO mode."""
        return self.yolo_remaining_seconds / 60

    def _is_yolo_expired(self) -> bool:
        """Check if YOLO mode has expired."""
        if not self._yolo_activated_at:
            return True
        elapsed = time.time() - self._yolo_activated_at
        return elapsed >= (self.yolo_duration_minutes * 60)

    def set_mode_change_callback(self, callback: Callable[[OperatingMode], None] | None) -> None:
        """Set a callback for mode changes.

        Args:
            callback: Function called when mode changes, receives new mode.
        """
        self._mode_change_callback = callback

    def set_mode(self, mode: OperatingMode) -> str:
        """Set the operating mode.

        Args:
            mode: The new operating mode.

        Returns:
            Status message about the mode change.
        """
        old_mode = self._current_mode
        self._current_mode = mode

        if mode == OperatingMode.YOLO:
            self._yolo_activated_at = time.time()
            message = (
                f"YOLO mode activated for {self.yolo_duration_minutes} minutes. "
                "All actions will be auto-approved. Be careful!"
            )
            logger.warning("YOLO mode activated for %d minutes", self.yolo_duration_minutes)
        elif mode == OperatingMode.CHAT:
            self._yolo_activated_at = None
            message = (
                "Chat mode activated. I can analyze and recommend, but I won't make "
                "any changes until you switch to Normal or YOLO mode."
            )
            logger.info("Chat mode activated")
        else:  # NORMAL
            self._yolo_activated_at = None
            message = (
                "Normal mode activated. I'll ask for confirmation before making "
                "significant changes."
            )
            logger.info("Normal mode activated")

        if self._mode_change_callback and old_mode != mode:
            self._mode_change_callback(mode)

        return message

    def check_tool_allowed(self, tool_name: str) -> tuple[bool, str]:
        """Check if a tool is allowed in the current mode.

        Args:
            tool_name: Name of the tool to check.

        Returns:
            Tuple of (allowed, message). If not allowed, message explains why.
        """
        mode = self.current_mode  # This checks YOLO expiry
        category = get_tool_category(tool_name)

        # Read-only tools are always allowed
        if category == ToolCategory.READ_ONLY:
            return (True, "")

        # In Chat mode, only read-only is allowed
        if mode == OperatingMode.CHAT:
            return (
                False,
                f"I'm in Chat mode and cannot execute '{tool_name}'. "
                "Switch to Normal mode ('enable normal mode') or YOLO mode "
                "('enable yolo mode') if you want me to make changes.",
            )

        # In Normal and YOLO mode, write operations are allowed
        return (True, "")

    def needs_confirmation(self, tool_name: str) -> bool:
        """Check if a tool needs user confirmation in Normal mode.

        In YOLO mode, nothing needs confirmation.
        In Chat mode, everything is blocked anyway.
        In Normal mode, destructive operations need confirmation.

        Args:
            tool_name: Name of the tool.

        Returns:
            True if confirmation is needed.
        """
        mode = self.current_mode
        if mode == OperatingMode.YOLO:
            return False
        if mode == OperatingMode.CHAT:
            return False  # Will be blocked anyway

        # In Normal mode, destructive operations need confirmation
        category = get_tool_category(tool_name)
        return category == ToolCategory.DESTRUCTIVE

    def get_status(self) -> dict[str, Any]:
        """Get current mode status.

        Returns:
            Dict with mode status information.
        """
        mode = self.current_mode  # This checks YOLO expiry
        status: dict[str, Any] = {
            "mode": mode.value,
            "mode_description": self._get_mode_description(mode),
        }

        if mode == OperatingMode.YOLO:
            status["yolo_remaining_seconds"] = self.yolo_remaining_seconds
            status["yolo_remaining_minutes"] = round(self.yolo_remaining_minutes, 1)

        return status

    def _get_mode_description(self, mode: OperatingMode) -> str:
        """Get a human-readable description of a mode."""
        descriptions = {
            OperatingMode.CHAT: "Read-only mode. Analysis and recommendations only.",
            OperatingMode.NORMAL: "Standard mode. Confirmation required for destructive actions.",
            OperatingMode.YOLO: "Auto-approve mode. All actions executed without confirmation.",
        }
        return descriptions.get(mode, "Unknown mode")

    def parse_mode_command(self, message: str) -> OperatingMode | None:
        """Parse a message for mode switching commands.

        Args:
            message: User message to parse.

        Returns:
            The requested mode, or None if not a mode command.
        """
        message_lower = message.lower().strip()

        # Chat mode patterns
        chat_patterns = [
            "enable chat mode",
            "switch to chat mode",
            "activate chat mode",
            "chat mode",
            "read only mode",
            "read-only mode",
        ]

        # Normal mode patterns
        normal_patterns = [
            "enable normal mode",
            "switch to normal mode",
            "activate normal mode",
            "normal mode",
            "disable yolo mode",
            "disable yolo",
            "exit yolo mode",
        ]

        # YOLO mode patterns
        yolo_patterns = [
            "enable yolo mode",
            "switch to yolo mode",
            "activate yolo mode",
            "yolo mode",
            "yolo",
        ]

        for pattern in chat_patterns:
            if pattern in message_lower:
                return OperatingMode.CHAT

        for pattern in normal_patterns:
            if pattern in message_lower:
                return OperatingMode.NORMAL

        for pattern in yolo_patterns:
            if pattern in message_lower:
                return OperatingMode.YOLO

        return None

    def is_mode_query(self, message: str) -> bool:
        """Check if the message is asking about the current mode.

        Args:
            message: User message.

        Returns:
            True if the message is a mode query.
        """
        message_lower = message.lower().strip()
        query_patterns = [
            "what mode",
            "which mode",
            "current mode",
            "what's my mode",
            "what is my mode",
            "mode status",
        ]
        return any(pattern in message_lower for pattern in query_patterns)

    def format_mode_response(self) -> str:
        """Format a response about the current mode.

        Returns:
            Human-readable mode status.
        """
        status = self.get_status()
        response = f"I'm currently in **{status['mode'].upper()}** mode.\n\n"
        response += f"{status['mode_description']}\n"

        if status["mode"] == "yolo":
            minutes = status.get("yolo_remaining_minutes", 0)
            response += f"\n⏱️ YOLO mode expires in {minutes:.1f} minutes."

        return response
