"""Telegram message handler for Mímir.

This module handles Telegram messages received via Home Assistant's
telegram_bot integration events.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any

from ..ha.types import Event, TelegramMessage
from ..utils.logging import get_logger

if TYPE_CHECKING:
    from ..ha.api import HomeAssistantAPI
    from ..ha.websocket import HomeAssistantWebSocket

logger = get_logger(__name__)

MessageHandler = Callable[[TelegramMessage], Coroutine[Any, Any, str | None]]


class TelegramHandler:
    """Handles Telegram messages from Home Assistant events.

    Listens for telegram_text and telegram_command events from the
    Home Assistant event bus (via WebSocket) and processes them.
    """

    def __init__(
        self,
        ha_api: HomeAssistantAPI,
        ha_ws: HomeAssistantWebSocket,
        owner_id: int,
    ) -> None:
        """Initialize the Telegram handler.

        Args:
            ha_api: Home Assistant API client for sending responses.
            ha_ws: Home Assistant WebSocket client for receiving events.
            owner_id: Telegram user ID of the owner (only this user is allowed).
        """
        self._ha_api = ha_api
        self._ha_ws = ha_ws
        self._owner_id = owner_id
        self._message_handler: MessageHandler | None = None

        # Register event handlers
        ha_ws.on_event("telegram_text", self._on_telegram_event)
        ha_ws.on_event("telegram_command", self._on_telegram_event)

    def set_message_handler(self, handler: MessageHandler) -> None:
        """Set the handler for incoming messages.

        Args:
            handler: Async function that takes a TelegramMessage and returns
                    the response text (or None for no response).
        """
        self._message_handler = handler

    async def _on_telegram_event(self, event: Event) -> None:
        """Handle incoming Telegram events."""
        try:
            message = TelegramMessage.from_event_data(event.data)
            logger.debug(
                "Received Telegram message: user_id=%d, text=%s",
                message.user_id,
                message.text[:50] if message.text else "",
            )

            # Validate sender
            if message.user_id != self._owner_id:
                logger.warning(
                    "Ignoring message from unauthorized user: %d (expected %d)",
                    message.user_id,
                    self._owner_id,
                )
                return

            # Process the message
            if self._message_handler:
                response = await self._message_handler(message)
                if response:
                    await self.send_message(response, message.chat_id)
            else:
                logger.warning("No message handler registered")

        except Exception as e:
            logger.exception("Error handling Telegram event: %s", e)

    async def send_message(
        self,
        text: str,
        chat_id: int,
        parse_mode: str = "Markdown",
    ) -> None:
        """Send a message to Telegram.

        Args:
            text: Message text.
            chat_id: Telegram chat ID.
            parse_mode: Parse mode for formatting (Markdown or HTML).
        """
        try:
            # Split long messages (Telegram limit is 4096 characters)
            max_length = 4000  # Leave some margin

            if len(text) <= max_length:
                await self._send_single_message(text, chat_id, parse_mode)
            else:
                # Split into multiple messages
                parts = self._split_message(text, max_length)
                for part in parts:
                    await self._send_single_message(part, chat_id, parse_mode)

        except Exception as e:
            logger.exception("Error sending Telegram message: %s", e)

    async def _send_single_message(
        self,
        text: str,
        chat_id: int,
        parse_mode: str,
    ) -> None:
        """Send a single message to Telegram."""
        await self._ha_api.call_service(
            domain="telegram_bot",
            service="send_message",
            service_data={
                "message": text,
                "target": chat_id,
                "parse_mode": parse_mode,
            },
        )
        logger.debug("Sent Telegram message to chat_id=%d", chat_id)

    def _split_message(self, text: str, max_length: int) -> list[str]:
        """Split a long message into multiple parts.

        Tries to split at paragraph boundaries, then sentences, then words.
        """
        if len(text) <= max_length:
            return [text]

        parts = []
        remaining = text

        while remaining:
            if len(remaining) <= max_length:
                parts.append(remaining)
                break

            # Find a good split point
            split_point = max_length

            # Try to split at paragraph boundary
            para_break = remaining.rfind("\n\n", 0, max_length)
            if para_break > max_length // 2:
                split_point = para_break + 2
            else:
                # Try to split at line boundary
                line_break = remaining.rfind("\n", 0, max_length)
                if line_break > max_length // 2:
                    split_point = line_break + 1
                else:
                    # Try to split at sentence boundary
                    for sep in [". ", "! ", "? "]:
                        sentence_break = remaining.rfind(sep, 0, max_length)
                        if sentence_break > max_length // 2:
                            split_point = sentence_break + len(sep)
                            break
                    else:
                        # Try to split at word boundary
                        word_break = remaining.rfind(" ", 0, max_length)
                        if word_break > max_length // 2:
                            split_point = word_break + 1

            parts.append(remaining[:split_point].rstrip())
            remaining = remaining[split_point:].lstrip()

        return parts

    async def send_notification(
        self,
        text: str,
        title: str | None = None,
    ) -> None:
        """Send a proactive notification to the owner.

        Args:
            text: Notification text.
            title: Optional title.
        """
        if title:
            message = f"*{title}*\n\n{text}"
        else:
            message = text

        # Send to owner's chat (using owner_id as chat_id for private chats)
        await self.send_message(message, self._owner_id)
