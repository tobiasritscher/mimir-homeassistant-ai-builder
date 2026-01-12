"""Proactive notification manager for Mímir.

Monitors Home Assistant for issues and notifies users via Telegram.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any

from ..utils.logging import get_logger

if TYPE_CHECKING:
    from ..ha.api import HomeAssistantAPI

logger = get_logger(__name__)


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DetectedIssue:
    """A detected issue that may warrant notification."""

    issue_type: str
    message: str
    priority: NotificationPriority
    entity_id: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def notification_text(self) -> str:
        """Format the issue for notification."""
        priority_emoji = {
            NotificationPriority.LOW: "ℹ️",
            NotificationPriority.MEDIUM: "⚠️",
            NotificationPriority.HIGH: "🔴",
            NotificationPriority.CRITICAL: "🚨",
        }

        emoji = priority_emoji.get(self.priority, "ℹ️")
        text = f"{emoji} **{self.issue_type}**\n\n{self.message}"

        if self.entity_id:
            text += f"\n\nEntity: `{self.entity_id}`"

        return text


@dataclass
class NotificationManager:
    """Manages proactive notifications for Home Assistant issues.

    Periodically monitors:
    - Error log for new errors
    - Unavailable entities
    - Failed automations

    Attributes:
        check_interval_minutes: How often to check for issues.
        enabled: Whether notifications are enabled.
    """

    ha_api: HomeAssistantAPI
    check_interval_minutes: int = 30
    enabled: bool = True

    # Track what we've already notified about
    _notified_errors: set[str] = field(default_factory=set)
    _notified_unavailable: set[str] = field(default_factory=set)
    _last_check: datetime | None = field(default=None)
    _last_log_hash: str = field(default="")

    # Callback for sending notifications
    _notification_callback: Any | None = field(default=None)

    # Background task
    _monitor_task: asyncio.Task[None] | None = field(default=None)
    _running: bool = field(default=False)

    def set_notification_callback(self, callback: Any) -> None:
        """Set the callback for sending notifications.

        The callback should accept a string message.

        Args:
            callback: Async function that sends a notification.
        """
        self._notification_callback = callback

    async def start(self) -> None:
        """Start the notification monitor."""
        if not self.enabled:
            logger.info("Proactive notifications disabled")
            return

        if self._running:
            logger.warning("Notification manager already running")
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(
            "Proactive notification manager started (interval: %d minutes)",
            self.check_interval_minutes,
        )

    async def stop(self) -> None:
        """Stop the notification monitor."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
        logger.info("Proactive notification manager stopped")

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        # Wait a bit before first check
        await asyncio.sleep(60)

        while self._running:
            try:
                await self._check_for_issues()
            except Exception as e:
                logger.exception("Error in notification monitor: %s", e)

            # Wait for next check
            await asyncio.sleep(self.check_interval_minutes * 60)

    async def _check_for_issues(self) -> None:
        """Check for issues and send notifications."""
        if not self._notification_callback:
            logger.debug("No notification callback set, skipping check")
            return

        logger.debug("Checking for issues...")
        issues: list[DetectedIssue] = []

        # Check error log
        try:
            log_issues = await self._check_error_log()
            issues.extend(log_issues)
        except Exception as e:
            logger.warning("Failed to check error log: %s", e)

        # Check for unavailable entities
        try:
            unavailable_issues = await self._check_unavailable_entities()
            issues.extend(unavailable_issues)
        except Exception as e:
            logger.warning("Failed to check unavailable entities: %s", e)

        # Send notifications for new issues
        for issue in issues:
            try:
                await self._notification_callback(issue.notification_text)
                logger.info("Sent notification for: %s", issue.issue_type)
            except Exception as e:
                logger.warning("Failed to send notification: %s", e)

        self._last_check = datetime.now()

    async def _check_error_log(self) -> list[DetectedIssue]:
        """Check the error log for new errors."""
        issues: list[DetectedIssue] = []

        try:
            log_content = await self.ha_api.get_error_log()
        except Exception as e:
            logger.warning("Failed to get error log: %s", e)
            return issues

        # Simple hash to detect changes
        log_hash = str(hash(log_content[-1000:] if len(log_content) > 1000 else log_content))
        if log_hash == self._last_log_hash:
            return issues
        self._last_log_hash = log_hash

        # Look for critical errors
        critical_patterns = [
            (r"ERROR.*HomeAssistant.*", NotificationPriority.HIGH),
            (r"ERROR.*Integration.*failed", NotificationPriority.HIGH),
            (r"ERROR.*Connection.*refused", NotificationPriority.MEDIUM),
            (r"ERROR.*Timeout", NotificationPriority.MEDIUM),
            (r"WARNING.*deprecated", NotificationPriority.LOW),
        ]

        # Get recent lines
        recent_lines = log_content.split("\n")[-100:]

        for line in recent_lines:
            for pattern, priority in critical_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Create a key to avoid duplicate notifications
                    error_key = line[:100]
                    if error_key not in self._notified_errors:
                        self._notified_errors.add(error_key)
                        # Keep the set from growing too large
                        if len(self._notified_errors) > 1000:
                            self._notified_errors = set(list(self._notified_errors)[-500:])

                        issues.append(
                            DetectedIssue(
                                issue_type="Error Log Alert",
                                message=line[:500],
                                priority=priority,
                            )
                        )
                        break  # Only one notification per line

        return issues

    async def _check_unavailable_entities(self) -> list[DetectedIssue]:
        """Check for unavailable entities."""
        issues: list[DetectedIssue] = []

        try:
            states = await self.ha_api.get_states()
        except Exception as e:
            logger.warning("Failed to get states: %s", e)
            return issues

        # Important domains to monitor
        important_domains = {"sensor", "binary_sensor", "switch", "light", "climate", "lock"}

        newly_unavailable = []
        for state in states:
            domain = state.entity_id.split(".")[0]
            if domain not in important_domains:
                continue

            if state.state == "unavailable":
                if state.entity_id not in self._notified_unavailable:
                    self._notified_unavailable.add(state.entity_id)
                    newly_unavailable.append(state.entity_id)
            else:
                # Entity is back, remove from notified set
                self._notified_unavailable.discard(state.entity_id)

        if newly_unavailable:
            # Group notifications
            if len(newly_unavailable) <= 3:
                for entity_id in newly_unavailable:
                    issues.append(
                        DetectedIssue(
                            issue_type="Entity Unavailable",
                            message=f"Entity `{entity_id}` is now unavailable.",
                            priority=NotificationPriority.MEDIUM,
                            entity_id=entity_id,
                        )
                    )
            else:
                # Many entities unavailable - might be a bigger issue
                entity_list = "\n".join(f"- `{e}`" for e in newly_unavailable[:10])
                more = f"\n... and {len(newly_unavailable) - 10} more" if len(newly_unavailable) > 10 else ""
                issues.append(
                    DetectedIssue(
                        issue_type="Multiple Entities Unavailable",
                        message=f"{len(newly_unavailable)} entities became unavailable:\n{entity_list}{more}",
                        priority=NotificationPriority.HIGH,
                    )
                )

        return issues

    async def check_now(self) -> list[DetectedIssue]:
        """Manually trigger an issue check and return found issues.

        Returns:
            List of detected issues.
        """
        issues: list[DetectedIssue] = []

        try:
            log_issues = await self._check_error_log()
            issues.extend(log_issues)
        except Exception as e:
            logger.warning("Failed to check error log: %s", e)

        try:
            unavailable_issues = await self._check_unavailable_entities()
            issues.extend(unavailable_issues)
        except Exception as e:
            logger.warning("Failed to check unavailable entities: %s", e)

        return issues

    def get_status(self) -> dict[str, Any]:
        """Get the current notification manager status.

        Returns:
            Status information.
        """
        return {
            "enabled": self.enabled,
            "running": self._running,
            "check_interval_minutes": self.check_interval_minutes,
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "notified_errors_count": len(self._notified_errors),
            "unavailable_entities_count": len(self._notified_unavailable),
        }
