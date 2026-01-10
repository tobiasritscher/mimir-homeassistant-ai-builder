"""Type definitions for Home Assistant integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class EntityState:
    """State of a Home Assistant entity."""

    entity_id: str
    state: str
    attributes: dict[str, Any]
    last_changed: datetime | None = None
    last_updated: datetime | None = None
    context: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EntityState:
        """Create EntityState from API response."""
        last_changed = None
        last_updated = None

        if "last_changed" in data:
            try:
                last_changed = datetime.fromisoformat(data["last_changed"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        if "last_updated" in data:
            try:
                last_updated = datetime.fromisoformat(data["last_updated"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        return cls(
            entity_id=data["entity_id"],
            state=data["state"],
            attributes=data.get("attributes", {}),
            last_changed=last_changed,
            last_updated=last_updated,
            context=data.get("context"),
        )


@dataclass
class Entity:
    """A Home Assistant entity definition."""

    entity_id: str
    name: str | None = None
    area_id: str | None = None
    device_id: str | None = None
    platform: str | None = None
    labels: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Entity:
        """Create Entity from API response."""
        return cls(
            entity_id=data["entity_id"],
            name=data.get("name"),
            area_id=data.get("area_id"),
            device_id=data.get("device_id"),
            platform=data.get("platform"),
            labels=data.get("labels", []),
        )


@dataclass
class Service:
    """A Home Assistant service definition."""

    domain: str
    service: str
    name: str | None = None
    description: str | None = None
    fields: dict[str, Any] = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        """Get the full service name (domain.service)."""
        return f"{self.domain}.{self.service}"

    @classmethod
    def from_dict(cls, domain: str, service: str, data: dict[str, Any]) -> Service:
        """Create Service from API response."""
        return cls(
            domain=domain,
            service=service,
            name=data.get("name"),
            description=data.get("description"),
            fields=data.get("fields", {}),
        )


@dataclass
class Event:
    """A Home Assistant event."""

    event_type: str
    data: dict[str, Any]
    origin: str | None = None
    time_fired: datetime | None = None
    context: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Event:
        """Create Event from WebSocket message."""
        time_fired = None
        if "time_fired" in data:
            try:
                time_fired = datetime.fromisoformat(data["time_fired"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        return cls(
            event_type=data.get("event_type", ""),
            data=data.get("data", {}),
            origin=data.get("origin"),
            time_fired=time_fired,
            context=data.get("context"),
        )


@dataclass
class Automation:
    """A Home Assistant automation."""

    id: str
    alias: str | None = None
    description: str | None = None
    trigger: list[dict[str, Any]] = field(default_factory=list)
    condition: list[dict[str, Any]] = field(default_factory=list)
    action: list[dict[str, Any]] = field(default_factory=list)
    mode: str = "single"


@dataclass
class Script:
    """A Home Assistant script."""

    id: str
    alias: str | None = None
    description: str | None = None
    sequence: list[dict[str, Any]] = field(default_factory=list)
    mode: str = "single"


@dataclass
class Scene:
    """A Home Assistant scene."""

    id: str
    name: str
    entities: dict[str, Any] = field(default_factory=dict)


@dataclass
class TelegramMessage:
    """A Telegram message from Home Assistant event."""

    message_id: int
    chat_id: int
    user_id: int
    text: str
    from_first_name: str | None = None
    from_last_name: str | None = None
    from_username: str | None = None
    date: datetime | None = None

    @classmethod
    def from_event_data(cls, data: dict[str, Any]) -> TelegramMessage:
        """Create TelegramMessage from event data."""
        date = None
        if "date" in data:
            try:
                date = datetime.fromtimestamp(data["date"])
            except (ValueError, TypeError):
                pass

        return cls(
            message_id=data.get("message_id", 0),
            chat_id=data.get("chat_id", 0),
            user_id=data.get("user_id", 0),
            text=data.get("text", ""),
            from_first_name=data.get("from_first_name"),
            from_last_name=data.get("from_last_name"),
            from_username=data.get("from_username"),
            date=date,
        )
