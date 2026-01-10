"""Mímir - Intelligent Home Assistant Agent.

Main entry point for the Mímir add-on.
"""

from __future__ import annotations

import asyncio
import contextlib
import signal
from typing import TYPE_CHECKING

from .config import load_config
from .conversation.manager import ConversationManager
from .ha.api import HomeAssistantAPI
from .ha.websocket import HomeAssistantWebSocket
from .llm.factory import create_provider
from .telegram.handler import TelegramHandler
from .tools.registry import ToolRegistry
from .tools.web_search import HACSSearchTool, HomeAssistantDocsSearchTool, WebSearchTool
from .utils.logging import get_logger, setup_logging

if TYPE_CHECKING:
    from .ha.types import TelegramMessage

logger = get_logger(__name__)


class MimirAgent:
    """The main Mímir agent application."""

    def __init__(self) -> None:
        """Initialize the Mímir agent."""
        # Load configuration
        self._config = load_config()

        # Initialize components
        self._llm = create_provider(self._config.llm)
        self._ha_api = HomeAssistantAPI()
        self._ha_ws = HomeAssistantWebSocket()
        self._tool_registry = ToolRegistry()
        self._telegram_handler: TelegramHandler | None = None
        self._conversation_manager: ConversationManager | None = None

        # Shutdown event
        self._shutdown_event = asyncio.Event()

        # Register tools
        self._register_tools()

    def _register_tools(self) -> None:
        """Register available tools."""
        self._tool_registry.register(WebSearchTool())
        self._tool_registry.register(HomeAssistantDocsSearchTool())
        self._tool_registry.register(HACSSearchTool())
        logger.info("Registered %d tools", len(self._tool_registry))

    async def _handle_telegram_message(self, message: TelegramMessage) -> str | None:
        """Handle an incoming Telegram message.

        Args:
            message: The Telegram message.

        Returns:
            Response text, or None.
        """
        if not self._conversation_manager:
            return "I'm still starting up. Please try again in a moment."

        if not message.text:
            return None

        # Process the message
        try:
            response = await self._conversation_manager.process_message(message.text)
            return response
        except Exception as e:
            logger.exception("Error processing message: %s", e)
            return f"An error occurred: {e}"

    async def _check_ha_connection(self) -> bool:
        """Check if Home Assistant is reachable."""
        try:
            if await self._ha_api.ping():
                logger.info("Home Assistant connection verified")
                return True
            else:
                logger.error("Home Assistant is not responding")
                return False
        except Exception as e:
            logger.error("Failed to connect to Home Assistant: %s", e)
            return False

    async def start(self) -> None:
        """Start the Mímir agent."""
        logger.info("Starting Mímir agent...")
        logger.info("LLM Provider: %s (%s)", self._llm.name, self._llm.model)
        logger.info("Operating Mode: %s", self._config.operating_mode.value)

        # Check HA connection
        if not await self._check_ha_connection():
            logger.error("Cannot start without Home Assistant connection")
            return

        # Initialize conversation manager
        self._conversation_manager = ConversationManager(
            llm=self._llm,
            tool_registry=self._tool_registry,
            operating_mode=self._config.operating_mode,
        )

        # Initialize Telegram handler
        self._telegram_handler = TelegramHandler(
            ha_api=self._ha_api,
            ha_ws=self._ha_ws,
            owner_id=self._config.telegram_owner_id,
        )
        self._telegram_handler.set_message_handler(self._handle_telegram_message)

        # Start WebSocket connection in background
        ws_task = asyncio.create_task(self._ha_ws.run())

        logger.info("Mímir is ready and listening for messages")

        # Wait for shutdown
        try:
            await self._shutdown_event.wait()
        except asyncio.CancelledError:
            pass
        finally:
            # Cleanup
            logger.info("Shutting down Mímir...")
            await self._ha_ws.stop()
            await self._ha_api.close()
            await self._llm.close()

            # Cancel WebSocket task
            ws_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await ws_task

        logger.info("Mímir shutdown complete")

    def shutdown(self) -> None:
        """Signal the agent to shut down."""
        self._shutdown_event.set()


async def main() -> None:
    """Main entry point."""
    # Setup logging
    setup_logging()

    logger.info("=" * 50)
    logger.info("Mímir - Intelligent Home Assistant Agent")
    logger.info("=" * 50)

    # Create and start the agent
    agent = MimirAgent()

    # Handle signals
    loop = asyncio.get_running_loop()

    def signal_handler() -> None:
        logger.info("Received shutdown signal")
        agent.shutdown()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    # Run the agent
    await agent.start()


if __name__ == "__main__":
    asyncio.run(main())
