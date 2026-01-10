"""Type definitions for the LLM abstraction layer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Role(str, Enum):
    """Message roles in a conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ToolCall:
    """Represents a tool call made by the LLM."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolResult:
    """Represents the result of a tool execution."""

    tool_call_id: str
    content: str
    is_error: bool = False


@dataclass
class ContentBlock:
    """A content block within a message."""

    type: str  # "text" or "tool_use" or "tool_result"
    text: str | None = None
    tool_call: ToolCall | None = None
    tool_result: ToolResult | None = None


@dataclass
class Message:
    """A message in a conversation."""

    role: Role
    content: str | list[ContentBlock]
    tool_calls: list[ToolCall] | None = None

    @classmethod
    def user(cls, content: str) -> Message:
        """Create a user message."""
        return cls(role=Role.USER, content=content)

    @classmethod
    def assistant(
        cls, content: str | None = None, tool_calls: list[ToolCall] | None = None
    ) -> Message:
        """Create an assistant message."""
        return cls(
            role=Role.ASSISTANT,
            content=content or "",
            tool_calls=tool_calls,
        )

    @classmethod
    def tool_result(cls, tool_call_id: str, content: str, is_error: bool = False) -> Message:
        """Create a tool result message."""
        result = ToolResult(
            tool_call_id=tool_call_id,
            content=content,
            is_error=is_error,
        )
        block = ContentBlock(type="tool_result", tool_result=result)
        return cls(role=Role.USER, content=[block])


@dataclass
class Tool:
    """Definition of a tool available to the LLM."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema

    def to_anthropic_format(self) -> dict[str, Any]:
        """Convert to Anthropic's tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }

    def to_openai_format(self) -> dict[str, Any]:
        """Convert to OpenAI's tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class StopReason(str, Enum):
    """Reasons why the LLM stopped generating."""

    END_TURN = "end_turn"
    TOOL_USE = "tool_use"
    MAX_TOKENS = "max_tokens"
    STOP_SEQUENCE = "stop_sequence"


@dataclass
class Usage:
    """Token usage statistics."""

    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.input_tokens + self.output_tokens


@dataclass
class Response:
    """Response from an LLM completion."""

    content: str | None
    tool_calls: list[ToolCall] | None
    stop_reason: StopReason
    usage: Usage
    model: str

    @property
    def has_tool_calls(self) -> bool:
        """Check if the response contains tool calls."""
        return self.tool_calls is not None and len(self.tool_calls) > 0


@dataclass
class ResponseChunk:
    """A streaming response chunk."""

    delta_content: str | None = None
    delta_tool_call: ToolCall | None = None
    is_final: bool = False
    response: Response | None = None  # Only set when is_final=True
