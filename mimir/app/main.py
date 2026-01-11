"""Mímir - Intelligent Home Assistant Agent.

Main entry point for the Mímir add-on.
"""

from __future__ import annotations

import asyncio
import contextlib
import signal
from typing import TYPE_CHECKING, Any

from aiohttp import web

from .config import load_config
from .conversation.manager import ConversationManager
from .db import AuditRepository, Database, MemoryRepository
from .git import GitManager
from .git.manager import GitConfig
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
from .tools.memory_tools import ForgetMemoryTool, RecallMemoriesTool, StoreMemoryTool
from .tools.registry import ToolRegistry
from .tools.web_search import HACSSearchTool, HomeAssistantDocsSearchTool, WebSearchTool
from .utils.logging import get_logger, setup_logging
from .web import request_logger_middleware, setup_routes

if TYPE_CHECKING:
    from .ha.types import TelegramMessage

from .ha.types import UserContext

logger = get_logger(__name__)


class MimirAgent:
    """The main Mímir agent application."""

    VERSION = "0.1.38"

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

        # Database, audit, and memory
        self._database: Database | None = None
        self._audit: AuditRepository | None = None
        self._memory: MemoryRepository | None = None

        # Git manager
        self._git: GitManager | None = None

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

        # Create user context from Telegram message
        user_context = UserContext.from_telegram_message(message)
        logger.info(
            "Telegram message from user: %s (%s)",
            user_context.friendly_name,
            user_context.user_id,
        )

        # Process the message with user context
        try:
            response = await self._conversation_manager.process_message(
                message.text,
                user_context=user_context,
            )
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

    async def _init_database(self) -> None:
        """Initialize database, audit, and memory repositories."""
        db_path = "/data/mimir.db"
        self._database = Database(db_path)
        await self._database.initialize()
        self._audit = AuditRepository(self._database)
        self._memory = MemoryRepository(self._database)

        # Register memory tools now that we have the repository
        self._tool_registry.register(StoreMemoryTool(self._memory))
        self._tool_registry.register(RecallMemoriesTool(self._memory))
        self._tool_registry.register(ForgetMemoryTool(self._memory))

        logger.info("Database initialized at %s", db_path)

    async def _init_git(self) -> None:
        """Initialize git manager."""
        git_config = GitConfig(
            repo_path="/config",
            author_name="Mimir",
            author_email="mimir@asgard.local",
            enabled=True,
        )
        self._git = GitManager(git_config)
        if await self._git.initialize():
            logger.info("Git repository initialized")
        else:
            logger.warning("Git initialization failed or disabled")

    def _create_tool_execution_callback(
        self,
    ) -> Any:
        """Create a callback for logging tool executions."""

        async def callback(
            tool_name: str,
            parameters: dict[str, Any],
            result: str | None,
            duration_ms: int,
            success: bool,
            error: str | None,
        ) -> None:
            if self._audit:
                await self._audit.log_tool_execution(
                    tool_name=tool_name,
                    parameters=parameters,
                    result=result,
                    duration_ms=duration_ms,
                    success=success,
                    error_message=error,
                )

        return callback

    async def _start_web_server(self) -> None:
        """Start the web server."""
        self._web_app = web.Application(middlewares=[request_logger_middleware])

        # Store references for handlers
        self._web_app["agent"] = self
        self._web_app["audit"] = self._audit
        self._web_app["git"] = self._git

        # Setup all routes
        setup_routes(self._web_app)

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
                logger.info(
                    "Retrying HA connection in %.1f seconds... (%d/%d)",
                    delay,
                    attempt + 1,
                    max_retries,
                )
                await asyncio.sleep(delay)
        return False

    async def start(self) -> None:
        """Start the Mímir agent."""
        logger.info("Starting Mímir agent v%s...", self.VERSION)
        logger.info("LLM Provider: %s (%s)", self._llm.name, self._llm.model)
        logger.info("Operating Mode: %s", self._config.operating_mode.value)

        # Initialize database and audit
        try:
            await self._init_database()
        except Exception as e:
            logger.warning("Failed to initialize database: %s", e)

        # Initialize git manager
        try:
            await self._init_git()
        except Exception as e:
            logger.warning("Failed to initialize git: %s", e)

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

        # Initialize conversation manager with audit and memory
        self._conversation_manager = ConversationManager(
            llm=self._llm,
            tool_registry=self._tool_registry,
            operating_mode=self._config.operating_mode,
            audit_repository=self._audit,
            memory_repository=self._memory,
        )

        # Load conversation history and memories from previous sessions
        await self._conversation_manager.load_history_from_audit()
        await self._conversation_manager.refresh_memory_summary()

        # Set up tool execution callback for audit logging
        self._tool_registry.set_execution_callback(self._create_tool_execution_callback())

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

            # Close database
            if self._database:
                await self._database.close()

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
