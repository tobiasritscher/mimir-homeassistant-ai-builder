"""Tests for Home Assistant types."""

from __future__ import annotations

from mimir.app.ha.types import Entity, EntityState, Event, Service, TelegramMessage


class TestEntityState:
    """Tests for EntityState class."""

    def test_from_dict_basic(self) -> None:
        """Test creating EntityState from dict."""
        data = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"brightness": 255, "friendly_name": "Living Room Light"},
        }
        state = EntityState.from_dict(data)

        assert state.entity_id == "light.living_room"
        assert state.state == "on"
        assert state.attributes["brightness"] == 255

    def test_from_dict_with_timestamps(self) -> None:
        """Test creating EntityState with timestamps."""
        data = {
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "attributes": {},
            "last_changed": "2025-01-10T12:00:00+00:00",
            "last_updated": "2025-01-10T12:00:00+00:00",
        }
        state = EntityState.from_dict(data)

        assert state.last_changed is not None
        assert state.last_updated is not None


class TestEntity:
    """Tests for Entity class."""

    def test_from_dict(self) -> None:
        """Test creating Entity from dict."""
        data = {
            "entity_id": "light.kitchen",
            "name": "Kitchen Light",
            "area_id": "kitchen",
            "device_id": "device123",
            "platform": "hue",
            "labels": ["indoor", "lighting"],
        }
        entity = Entity.from_dict(data)

        assert entity.entity_id == "light.kitchen"
        assert entity.name == "Kitchen Light"
        assert entity.area_id == "kitchen"
        assert entity.labels == ["indoor", "lighting"]


class TestService:
    """Tests for Service class."""

    def test_full_name(self) -> None:
        """Test full service name."""
        service = Service(
            domain="light",
            service="turn_on",
            name="Turn on",
            description="Turn on a light",
        )
        assert service.full_name == "light.turn_on"

    def test_from_dict(self) -> None:
        """Test creating Service from dict."""
        data = {
            "name": "Turn off",
            "description": "Turn off a light",
            "fields": {"transition": {"description": "Transition time"}},
        }
        service = Service.from_dict("light", "turn_off", data)

        assert service.domain == "light"
        assert service.service == "turn_off"
        assert service.name == "Turn off"


class TestEvent:
    """Tests for Event class."""

    def test_from_dict(self) -> None:
        """Test creating Event from dict."""
        data = {
            "event_type": "state_changed",
            "data": {"entity_id": "light.living_room", "new_state": {"state": "on"}},
            "origin": "LOCAL",
        }
        event = Event.from_dict(data)

        assert event.event_type == "state_changed"
        assert event.data["entity_id"] == "light.living_room"
        assert event.origin == "LOCAL"


class TestTelegramMessage:
    """Tests for TelegramMessage class."""

    def test_from_event_data(self) -> None:
        """Test creating TelegramMessage from event data."""
        data = {
            "message_id": 12345,
            "chat_id": 67890,
            "user_id": 11111,
            "text": "Hello Mímir!",
            "from_first_name": "John",
            "from_username": "johndoe",
        }
        message = TelegramMessage.from_event_data(data)

        assert message.message_id == 12345
        assert message.chat_id == 67890
        assert message.user_id == 11111
        assert message.text == "Hello Mímir!"
        assert message.from_first_name == "John"
        assert message.from_username == "johndoe"
