"""Rate limiter for Mímir tool executions.

Tracks and limits destructive operations to prevent runaway modifications.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum


class OperationType(Enum):
    """Types of operations for rate limiting."""

    DELETION = "deletion"
    MODIFICATION = "modification"


@dataclass
class RateLimiter:
    """Rate limiter for tracking and limiting operations.

    Tracks operations in a sliding window (default 1 hour) and rejects
    operations that exceed the configured limits.
    """

    deletions_per_hour: int = 5
    modifications_per_hour: int = 20
    window_seconds: int = 3600  # 1 hour

    # Track timestamps of operations
    _deletion_times: deque[float] = field(default_factory=deque)
    _modification_times: deque[float] = field(default_factory=deque)

    def _cleanup_old_entries(self, times: deque[float]) -> None:
        """Remove entries older than the window."""
        cutoff = time.time() - self.window_seconds
        while times and times[0] < cutoff:
            times.popleft()

    def check_allowed(self, operation_type: OperationType) -> tuple[bool, str]:
        """Check if an operation is allowed under rate limits.

        Args:
            operation_type: Type of operation to check.

        Returns:
            Tuple of (allowed, message). If not allowed, message explains why.
        """
        if operation_type == OperationType.DELETION:
            self._cleanup_old_entries(self._deletion_times)
            current_count = len(self._deletion_times)

            if current_count >= self.deletions_per_hour:
                return (
                    False,
                    f"Rate limit exceeded: {current_count}/{self.deletions_per_hour} "
                    f"deletions in the last hour. Please wait before deleting more items.",
                )
            return (True, "")

        elif operation_type == OperationType.MODIFICATION:
            self._cleanup_old_entries(self._modification_times)
            current_count = len(self._modification_times)

            if current_count >= self.modifications_per_hour:
                return (
                    False,
                    f"Rate limit exceeded: {current_count}/{self.modifications_per_hour} "
                    f"modifications in the last hour. Please wait before making more changes.",
                )
            return (True, "")

        return (True, "")

    def record_operation(self, operation_type: OperationType) -> None:
        """Record that an operation was performed.

        Args:
            operation_type: Type of operation performed.
        """
        now = time.time()

        if operation_type == OperationType.DELETION:
            self._deletion_times.append(now)
        elif operation_type == OperationType.MODIFICATION:
            self._modification_times.append(now)

    def get_status(self) -> dict[str, int]:
        """Get current rate limit status.

        Returns:
            Dict with current counts and limits.
        """
        self._cleanup_old_entries(self._deletion_times)
        self._cleanup_old_entries(self._modification_times)

        return {
            "deletions_used": len(self._deletion_times),
            "deletions_limit": self.deletions_per_hour,
            "modifications_used": len(self._modification_times),
            "modifications_limit": self.modifications_per_hour,
        }

    def reset(self) -> None:
        """Reset all rate limit counters."""
        self._deletion_times.clear()
        self._modification_times.clear()


# Tool names and their operation types
TOOL_OPERATION_TYPES: dict[str, OperationType] = {
    # Deletion tools
    "delete_automation": OperationType.DELETION,
    "delete_script": OperationType.DELETION,
    "delete_scene": OperationType.DELETION,
    "delete_helper": OperationType.DELETION,
    "forget_memory": OperationType.DELETION,
    # Modification tools (create/update)
    "create_automation": OperationType.MODIFICATION,
    "update_automation": OperationType.MODIFICATION,
    "create_script": OperationType.MODIFICATION,
    "update_script": OperationType.MODIFICATION,
    "create_scene": OperationType.MODIFICATION,
    "update_scene": OperationType.MODIFICATION,
    "create_helper": OperationType.MODIFICATION,
    "store_memory": OperationType.MODIFICATION,
    "call_service": OperationType.MODIFICATION,
}


def get_operation_type(tool_name: str) -> OperationType | None:
    """Get the operation type for a tool.

    Args:
        tool_name: Name of the tool.

    Returns:
        Operation type, or None if tool is not rate-limited.
    """
    return TOOL_OPERATION_TYPES.get(tool_name)
