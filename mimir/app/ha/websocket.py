"""WebSocket client for Home Assistant real-time events."""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Callable, Coroutine
from typing import Any

import aiohttp

from ..utils.logging import get_logger
from .types import Event

logger = get_logger(__name__)

EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class HomeAssistantWebSocket:
    """WebSocket client for Home Assistant.

    Connects to Home Assistant's WebSocket API for real-time events.
    Used primarily to receive Telegram message events.
    """

    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
    ) -> None:
        """Initialize the WebSocket client.

        Args:
            url: WebSocket URL. If None, uses Supervisor proxy.
            token: Access token. If None, uses SUPERVISOR_TOKEN.
        """
        # Detect add-on environment
        supervisor_token = os.environ.get("SUPERVISOR_TOKEN")

        if supervisor_token and not url:
            # Running as add-on with token - use Supervisor proxy
            self._ws_url = "ws://supervisor/core/websocket"
            self._token = supervisor_token
            logger.info("Using Supervisor WebSocket proxy")
        elif not url:
            # Running as add-on without token - try internal Docker network
            self._ws_url = "ws://homeassistant:8123/api/websocket"
            self._token = supervisor_token or ""
            logger.info("Using internal Docker WebSocket: %s", self._ws_url)
        else:
            # Explicit URL provided
            self._ws_url = f"{url.rstrip('/')}/api/websocket"
            self._token = token or ""
            logger.info("Using direct WebSocket connection: %s", self._ws_url)

        self._session: aiohttp.ClientSession | None = None
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._message_id = 0
        self._handlers: dict[str, list[EventHandler]] = {}
        self._subscriptions: dict[int, str] = {}  # message_id -> event_type
        self._running = False
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 60.0

    def _next_id(self) -> int:
        """Get the next message ID."""
        self._message_id += 1
        return self._message_id

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure we have an active session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def connect(self) -> bool:
        """Connect to the WebSocket and authenticate."""
        session = await self._ensure_session()

        try:
            logger.info("Connecting to WebSocket: %s", self._ws_url)
            self._ws = await session.ws_connect(self._ws_url)

            # Wait for auth_required
            msg = await self._ws.receive()
            if msg.type != aiohttp.WSMsgType.TEXT:
                logger.error("Unexpected message type: %s", msg.type)
                return False

            data = json.loads(msg.data)
            if data.get("type") != "auth_required":
                logger.error("Expected auth_required, got: %s", data.get("type"))
                return False

            # Send auth
            await self._ws.send_json({"type": "auth", "access_token": self._token})

            # Wait for auth response
            msg = await self._ws.receive()
            if msg.type != aiohttp.WSMsgType.TEXT:
                logger.error("Unexpected message type: %s", msg.type)
                return False

            data = json.loads(msg.data)
            if data.get("type") == "auth_ok":
                logger.info("WebSocket authenticated successfully")
                self._reconnect_delay = 1.0  # Reset on successful connect
                return True
            else:
                logger.error("Authentication failed: %s", data)
                return False

        except aiohttp.ClientError as e:
            logger.error("WebSocket connection failed: %s", e)
            return False

    async def subscribe_events(self, event_type: str | None = None) -> int | None:
        """Subscribe to events.

        Args:
            event_type: Specific event type to subscribe to, or None for all.

        Returns:
            Subscription ID, or None if failed.
        """
        if not self._ws or self._ws.closed:
            logger.error("WebSocket not connected")
            return None

        msg_id = self._next_id()
        subscribe_msg: dict[str, Any] = {
            "id": msg_id,
            "type": "subscribe_events",
        }
        if event_type:
            subscribe_msg["event_type"] = event_type

        await self._ws.send_json(subscribe_msg)

        # Wait for confirmation
        async for msg in self._ws:
            if msg.type != aiohttp.WSMsgType.TEXT:
                continue

            data = json.loads(msg.data)
            if data.get("id") == msg_id:
                if data.get("type") == "result" and data.get("success"):
                    self._subscriptions[msg_id] = event_type or "*"
                    logger.info("Subscribed to events: %s (id=%d)", event_type or "all", msg_id)
                    return msg_id
                else:
                    logger.error("Subscription failed: %s", data)
                    return None

        return None

    def on_event(self, event_type: str, handler: EventHandler) -> None:
        """Register an event handler.

        Args:
            event_type: Event type to handle (e.g., "telegram_text").
            handler: Async function to call when event is received.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug("Registered handler for event: %s", event_type)

    async def _dispatch_event(self, event: Event) -> None:
        """Dispatch an event to registered handlers."""
        handlers = self._handlers.get(event.event_type, [])
        handlers.extend(self._handlers.get("*", []))  # Catch-all handlers

        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.exception("Error in event handler for %s: %s", event.event_type, e)

    async def _listen_loop(self) -> None:
        """Main loop for receiving messages."""
        if not self._ws:
            return

        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)

                    if data.get("type") == "event":
                        event_data = data.get("event", {})
                        event = Event.from_dict(event_data)
                        await self._dispatch_event(event)

                    elif data.get("type") == "result":
                        # Handle command results if needed
                        pass

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error("WebSocket error: %s", msg.data)
                    break

                elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED):
                    logger.warning("WebSocket closed")
                    break

        except asyncio.CancelledError:
            logger.info("WebSocket listen loop cancelled")
            raise
        except Exception as e:
            logger.exception("Error in WebSocket listen loop: %s", e)

    async def run(self) -> None:
        """Run the WebSocket client with automatic reconnection."""
        self._running = True

        while self._running:
            try:
                if await self.connect():
                    # Subscribe to Telegram events
                    await self.subscribe_events("telegram_text")
                    await self.subscribe_events("telegram_command")

                    # Run the listen loop
                    await self._listen_loop()

                if not self._running:
                    break

                # Reconnect with backoff
                logger.info("Reconnecting in %.1f seconds...", self._reconnect_delay)
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)

            except asyncio.CancelledError:
                logger.info("WebSocket client cancelled")
                break
            except Exception as e:
                logger.exception("Unexpected error in WebSocket client: %s", e)
                await asyncio.sleep(self._reconnect_delay)

    async def send_command(
        self,
        command_type: str,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        """Send a command and wait for the result.

        Args:
            command_type: The command type (e.g., "call_service").
            **kwargs: Additional command parameters.

        Returns:
            The result data, or None if failed.
        """
        if not self._ws or self._ws.closed:
            logger.error("WebSocket not connected")
            return None

        msg_id = self._next_id()
        command = {"id": msg_id, "type": command_type, **kwargs}

        await self._ws.send_json(command)

        # Wait for result (with timeout)
        try:
            async with asyncio.timeout(30):
                async for msg in self._ws:
                    if msg.type != aiohttp.WSMsgType.TEXT:
                        continue

                    data = json.loads(msg.data)
                    if data.get("id") == msg_id:
                        if data.get("success"):
                            result: dict[str, Any] | None = data.get("result")
                            return result
                        else:
                            logger.error("Command failed: %s", data.get("error"))
                            return None
        except TimeoutError:
            logger.error("Command timed out")
            return None

        return None

    async def call_service(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any] | None = None,
        target: dict[str, Any] | None = None,
    ) -> bool:
        """Call a Home Assistant service via WebSocket.

        Args:
            domain: Service domain.
            service: Service name.
            service_data: Service data.
            target: Target entities/areas/devices.

        Returns:
            True if successful.
        """
        command: dict[str, Any] = {
            "domain": domain,
            "service": service,
        }
        if service_data:
            command["service_data"] = service_data
        if target:
            command["target"] = target

        result = await self.send_command("call_service", **command)
        return result is not None

    async def stop(self) -> None:
        """Stop the WebSocket client."""
        self._running = False

        if self._ws and not self._ws.closed:
            await self._ws.close()
            self._ws = None

        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

        logger.info("WebSocket client stopped")
