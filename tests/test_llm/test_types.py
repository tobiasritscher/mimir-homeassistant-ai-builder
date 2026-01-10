"""Tests for LLM types."""

from __future__ import annotations

import pytest

from mimir.app.llm.types import (
    ContentBlock,
    Message,
    Response,
    Role,
    StopReason,
    Tool,
    ToolCall,
    ToolResult,
    Usage,
)


class TestMessage:
    """Tests for Message class."""

    def test_user_message(self) -> None:
        """Test creating a user message."""
        msg = Message.user("Hello")
        assert msg.role == Role.USER
        assert msg.content == "Hello"
        assert msg.tool_calls is None

    def test_assistant_message(self) -> None:
        """Test creating an assistant message."""
        msg = Message.assistant("Hi there!")
        assert msg.role == Role.ASSISTANT
        assert msg.content == "Hi there!"
        assert msg.tool_calls is None

    def test_assistant_message_with_tool_calls(self) -> None:
        """Test creating an assistant message with tool calls."""
        tool_call = ToolCall(id="1", name="test", arguments={"key": "value"})
        msg = Message.assistant(content="Using a tool", tool_calls=[tool_call])
        assert msg.role == Role.ASSISTANT
        assert msg.tool_calls is not None
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0].name == "test"

    def test_tool_result_message(self) -> None:
        """Test creating a tool result message."""
        msg = Message.tool_result(tool_call_id="1", content="Result", is_error=False)
        assert msg.role == Role.USER
        assert isinstance(msg.content, list)
        assert len(msg.content) == 1
        assert msg.content[0].type == "tool_result"


class TestTool:
    """Tests for Tool class."""

    def test_to_anthropic_format(self) -> None:
        """Test converting to Anthropic format."""
        tool = Tool(
            name="test_tool",
            description="A test tool",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        )
        anthropic_format = tool.to_anthropic_format()

        assert anthropic_format["name"] == "test_tool"
        assert anthropic_format["description"] == "A test tool"
        assert "input_schema" in anthropic_format

    def test_to_openai_format(self) -> None:
        """Test converting to OpenAI format."""
        tool = Tool(
            name="test_tool",
            description="A test tool",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        )
        openai_format = tool.to_openai_format()

        assert openai_format["type"] == "function"
        assert openai_format["function"]["name"] == "test_tool"
        assert openai_format["function"]["description"] == "A test tool"


class TestResponse:
    """Tests for Response class."""

    def test_has_tool_calls_true(self) -> None:
        """Test has_tool_calls when there are tool calls."""
        tool_call = ToolCall(id="1", name="test", arguments={})
        response = Response(
            content=None,
            tool_calls=[tool_call],
            stop_reason=StopReason.TOOL_USE,
            usage=Usage(input_tokens=10, output_tokens=5),
            model="test-model",
        )
        assert response.has_tool_calls is True

    def test_has_tool_calls_false(self) -> None:
        """Test has_tool_calls when there are no tool calls."""
        response = Response(
            content="Hello",
            tool_calls=None,
            stop_reason=StopReason.END_TURN,
            usage=Usage(input_tokens=10, output_tokens=5),
            model="test-model",
        )
        assert response.has_tool_calls is False

    def test_has_tool_calls_empty_list(self) -> None:
        """Test has_tool_calls with empty list."""
        response = Response(
            content="Hello",
            tool_calls=[],
            stop_reason=StopReason.END_TURN,
            usage=Usage(input_tokens=10, output_tokens=5),
            model="test-model",
        )
        assert response.has_tool_calls is False


class TestUsage:
    """Tests for Usage class."""

    def test_total_tokens(self) -> None:
        """Test total token calculation."""
        usage = Usage(input_tokens=100, output_tokens=50)
        assert usage.total_tokens == 150
