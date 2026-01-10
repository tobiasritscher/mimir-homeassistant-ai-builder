"""Mímir - Intelligent Home Assistant Agent.

Main entry point for the Mímir add-on.
"""

from __future__ import annotations

import asyncio
import contextlib
import signal
from typing import TYPE_CHECKING

from aiohttp import web

from .config import load_config
from .conversation.manager import ConversationManager
from .ha.api import HomeAssistantAPI
from .ha.websocket import HomeAssistantWebSocket
from .llm.factory import create_provider
from .telegram.handler import TelegramHandler
from .tools.ha_tools import (
    CallServiceTool,
    CreateAutomationTool,
    DeleteAutomationTool,
    GetAutomationConfigTool,
    GetAutomationsTool,
    GetEntitiesTool,
    GetEntityStateTool,
    GetErrorLogTool,
    GetLogbookTool,
    GetServicesTool,
    UpdateAutomationTool,
)
from .tools.registry import ToolRegistry
from .tools.web_search import HACSSearchTool, HomeAssistantDocsSearchTool, WebSearchTool
from .utils.logging import get_logger, setup_logging

if TYPE_CHECKING:
    from .ha.types import TelegramMessage

logger = get_logger(__name__)

# Web interface HTML template
STATUS_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Mímir - Home Assistant Agent</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        h1 {{
            color: #6366f1;
            border-bottom: 2px solid #6366f1;
            padding-bottom: 10px;
        }}
        .status-card {{
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }}
        .status-item {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .status-item:last-child {{
            border-bottom: none;
        }}
        .status-ok {{ color: #22c55e; }}
        .status-error {{ color: #ef4444; }}
        .status-pending {{ color: #f59e0b; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Mímir</h1>
        <p>Intelligent Home Assistant Agent with Nordic Wisdom</p>

        <div class="status-card">
            <h2>Status</h2>
            <div class="status-item">
                <span>Version</span>
                <span>{version}</span>
            </div>
            <div class="status-item">
                <span>LLM Provider</span>
                <span>{llm_provider}</span>
            </div>
            <div class="status-item">
                <span>LLM Model</span>
                <span>{llm_model}</span>
            </div>
            <div class="status-item">
                <span>Operating Mode</span>
                <span>{operating_mode}</span>
            </div>
            <div class="status-item">
                <span>Home Assistant</span>
                <span class="{ha_status_class}">{ha_status}</span>
            </div>
            <div class="status-item">
                <span>WebSocket</span>
                <span class="{ws_status_class}">{ws_status}</span>
            </div>
            <div class="status-item">
                <span>Telegram Owner ID</span>
                <span>{telegram_owner_id}</span>
            </div>
            <div class="status-item">
                <span>Registered Tools</span>
                <span>{tool_count}</span>
            </div>
        </div>

        <div class="status-card">
            <h2>Usage</h2>
            <p>Send a message to Mímir via Telegram to get started.</p>
            <p>Make sure your Telegram bot is configured in Home Assistant and your user ID matches the configured owner ID.</p>
        </div>
    </div>
</body>
</html>
"""


class MimirAgent:
    """The main Mímir agent application."""

    VERSION = "0.1.10"

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

        # Status tracking
        self._ha_connected = False
        self._ws_connected = False

        # Web server
        self._web_app: web.Application | None = None
        self._web_runner: web.AppRunner | None = None

        # Shutdown event
        self._shutdown_event = asyncio.Event()

        # Register tools
        self._register_tools()

    def _register_tools(self) -> None:
        """Register available tools."""
        # Web search tools
        self._tool_registry.register(WebSearchTool())
        self._tool_registry.register(HomeAssistantDocsSearchTool())
        self._tool_registry.register(HACSSearchTool())

        # Home Assistant tools
        self._tool_registry.register(GetEntitiesTool(self._ha_api))
        self._tool_registry.register(GetEntityStateTool(self._ha_api))
        self._tool_registry.register(GetAutomationsTool(self._ha_api))
        self._tool_registry.register(GetAutomationConfigTool(self._ha_api))
        self._tool_registry.register(CreateAutomationTool(self._ha_api))
        self._tool_registry.register(UpdateAutomationTool(self._ha_api))
        self._tool_registry.register(DeleteAutomationTool(self._ha_api))
        self._tool_registry.register(CallServiceTool(self._ha_api))
        self._tool_registry.register(GetServicesTool(self._ha_api))
        self._tool_registry.register(GetErrorLogTool(self._ha_api))
        self._tool_registry.register(GetLogbookTool(self._ha_api))

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
                self._ha_connected = True
                return True
            else:
                logger.error("Home Assistant is not responding")
                self._ha_connected = False
                return False
        except Exception as e:
            logger.error("Failed to connect to Home Assistant: %s", e)
            self._ha_connected = False
            return False

    async def _handle_status_request(self, _request: web.Request) -> web.Response:
        """Handle web status page request."""
        html = STATUS_HTML.format(
            version=self.VERSION,
            llm_provider=self._llm.name,
            llm_model=self._llm.model,
            operating_mode=self._config.operating_mode.value,
            ha_status="Connected" if self._ha_connected else "Disconnected",
            ha_status_class="status-ok" if self._ha_connected else "status-error",
            ws_status="Connected" if self._ws_connected else "Disconnected",
            ws_status_class="status-ok" if self._ws_connected else "status-error",
            telegram_owner_id=self._config.telegram_owner_id,
            tool_count=len(self._tool_registry),
        )
        return web.Response(text=html, content_type="text/html")

    async def _handle_health_request(self, _request: web.Request) -> web.Response:
        """Handle health check request."""
        return web.json_response({
            "status": "ok",
            "version": self.VERSION,
            "ha_connected": self._ha_connected,
            "ws_connected": self._ws_connected,
        })

    async def _start_web_server(self) -> None:
        """Start the web server."""
        self._web_app = web.Application()
        self._web_app.router.add_get("/", self._handle_status_request)
        self._web_app.router.add_get("/health", self._handle_health_request)

        self._web_runner = web.AppRunner(self._web_app)
        await self._web_runner.setup()

        site = web.TCPSite(self._web_runner, "0.0.0.0", 5000)
        await site.start()
        logger.info("Web interface started on http://0.0.0.0:5000")

    async def _stop_web_server(self) -> None:
        """Stop the web server."""
        if self._web_runner:
            await self._web_runner.cleanup()
            logger.info("Web server stopped")

    async def _connect_ha_with_retry(self, max_retries: int = 5, delay: float = 5.0) -> bool:
        """Try to connect to Home Assistant with retries."""
        for attempt in range(max_retries):
            if await self._check_ha_connection():
                return True
            if attempt < max_retries - 1:
                logger.info("Retrying HA connection in %.1f seconds... (%d/%d)", delay, attempt + 1, max_retries)
                await asyncio.sleep(delay)
        return False

    async def start(self) -> None:
        """Start the Mímir agent."""
        logger.info("Starting Mímir agent v%s...", self.VERSION)
        logger.info("LLM Provider: %s (%s)", self._llm.name, self._llm.model)
        logger.info("Operating Mode: %s", self._config.operating_mode.value)

        # Start web server first (so user can see status)
        await self._start_web_server()

        # Check HA connection with retries
        if not await self._connect_ha_with_retry():
            logger.error("Failed to connect to Home Assistant after retries")
            logger.info("Web interface still available at http://0.0.0.0:5000")
            # Don't exit - keep running so user can see status
            await self._shutdown_event.wait()
            await self._stop_web_server()
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
        async def ws_wrapper() -> None:
            try:
                self._ws_connected = True
                await self._ha_ws.run()
            except Exception as e:
                logger.error("WebSocket error: %s", e)
            finally:
                self._ws_connected = False

        ws_task = asyncio.create_task(ws_wrapper())

        logger.info("Mímir is ready and listening for messages")

        # Wait for shutdown
        try:
            await self._shutdown_event.wait()
        except asyncio.CancelledError:
            pass
        finally:
            # Cleanup
            logger.info("Shutting down Mímir...")
            await self._stop_web_server()
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
