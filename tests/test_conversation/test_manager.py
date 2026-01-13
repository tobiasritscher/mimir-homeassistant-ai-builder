"""Tests for the conversation manager."""

from __future__ import annotations

import pytest

from mimir.app.config import OperatingMode
from mimir.app.conversation.manager import ConversationManager
from mimir.app.llm.types import Response, StopReason, ToolCall, Usage
from mimir.app.tools.registry import ToolRegistry

from ..conftest import MockAuditLogEntry, MockAuditRepository, MockLLMProvider, MockTool


class TestConversationManager:
    """Tests for ConversationManager class."""

    @pytest.fixture
    def manager(self) -> ConversationManager:
        """Create a conversation manager with mocks."""
        llm = MockLLMProvider()
        registry = ToolRegistry()
        registry.register(MockTool())

        return ConversationManager(
            llm=llm,
            tool_registry=registry,
            operating_mode=OperatingMode.NORMAL,
        )

    @pytest.mark.asyncio
    async def test_process_simple_message(self, manager: ConversationManager) -> None:
        """Test processing a simple message without tool calls."""
        response = await manager.process_message("Hello!")

        assert response == "Mock response"

    @pytest.mark.asyncio
    async def test_process_message_with_tool_call(self) -> None:
        """Test processing a message that requires tool calls."""
        # Create responses: first with tool call, then final response
        tool_call = ToolCall(id="1", name="mock_tool", arguments={"query": "test"})
        responses = [
            Response(
                content=None,
                tool_calls=[tool_call],
                stop_reason=StopReason.TOOL_USE,
                usage=Usage(input_tokens=10, output_tokens=5),
                model="mock",
            ),
            Response(
                content="Here's the result from the tool!",
                tool_calls=None,
                stop_reason=StopReason.END_TURN,
                usage=Usage(input_tokens=20, output_tokens=10),
                model="mock",
            ),
        ]

        llm = MockLLMProvider(responses=responses)
        registry = ToolRegistry()
        registry.register(MockTool(result="Tool executed successfully"))

        manager = ConversationManager(
            llm=llm,
            tool_registry=registry,
            operating_mode=OperatingMode.NORMAL,
        )

        response = await manager.process_message("Use the tool")

        assert response == "Here's the result from the tool!"
        assert len(llm.calls) == 2  # Initial call + after tool execution

    def test_operating_mode_getter(self, manager: ConversationManager) -> None:
        """Test getting operating mode."""
        assert manager.operating_mode == OperatingMode.NORMAL

    def test_operating_mode_setter(self, manager: ConversationManager) -> None:
        """Test setting operating mode."""
        manager.operating_mode = OperatingMode.CHAT

        assert manager.operating_mode == OperatingMode.CHAT

    def test_clear_history(self, manager: ConversationManager) -> None:
        """Test clearing conversation history."""
        # Add some messages by processing
        # (In real tests, we'd check internal state)
        manager.clear_history()
        # Should not raise

    @pytest.mark.asyncio
    async def test_get_context_summary(self, manager: ConversationManager) -> None:
        """Test getting context summary."""
        summary = await manager.get_context_summary()

        assert "Operating mode: normal" in summary
        assert "mock_tool" in summary
        assert "messages" in summary

    @pytest.mark.asyncio
    async def test_load_history_from_audit(self) -> None:
        """Test loading conversation history from audit database."""
        test_user_id = "test_user_123"

        # Create mock audit logs (newest first, like the real DB returns)
        mock_logs = [
            MockAuditLogEntry(
                id=4,
                timestamp="2025-01-11T12:03:00",
                source="telegram",
                message_type="assistant",
                content="Der Schalter heißt switch.stecker_tv_station",
                user_id=test_user_id,
            ),
            MockAuditLogEntry(
                id=3,
                timestamp="2025-01-11T12:02:00",
                source="telegram",
                message_type="user",
                content="Welcher Schalter steuert die Lautsprecher?",
                user_id=test_user_id,
            ),
            MockAuditLogEntry(
                id=2,
                timestamp="2025-01-11T12:01:00",
                source="telegram",
                message_type="assistant",
                content="Hallo! Wie kann ich helfen?",
                user_id=test_user_id,
            ),
            MockAuditLogEntry(
                id=1,
                timestamp="2025-01-11T12:00:00",
                source="telegram",
                message_type="user",
                content="Hallo Mimir",
                user_id=test_user_id,
            ),
        ]

        audit = MockAuditRepository(logs=mock_logs)
        llm = MockLLMProvider()
        registry = ToolRegistry()

        manager = ConversationManager(
            llm=llm,
            tool_registry=registry,
            operating_mode=OperatingMode.NORMAL,
            audit_repository=audit,  # type: ignore[arg-type]
        )

        # Load history for specific user
        loaded = await manager.load_history_from_audit(user_id=test_user_id, limit=10)

        assert loaded == 4
        history = manager.get_history(user_id=test_user_id)
        assert len(history) == 4

        # Check order is chronological (oldest first)
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hallo Mimir"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Hallo! Wie kann ich helfen?"
        assert history[2]["role"] == "user"
        assert "Lautsprecher" in history[2]["content"]
        assert history[3]["role"] == "assistant"
        assert "switch.stecker_tv_station" in history[3]["content"]

    @pytest.mark.asyncio
    async def test_load_history_without_audit(self, manager: ConversationManager) -> None:
        """Test that load_history returns 0 when no audit repository."""
        loaded = await manager.load_history_from_audit(user_id="test_user")
        assert loaded == 0
