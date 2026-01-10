"""Pytest configuration and fixtures for Mímir tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from mimir.app.config import LLMConfig, LLMProvider, MimirConfig
from mimir.app.llm.base import LLMProvider as LLMProviderBase
from mimir.app.llm.types import Message, Response, ResponseChunk, StopReason, Tool, Usage
from mimir.app.tools.base import BaseTool
from mimir.app.tools.registry import ToolRegistry

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@pytest.fixture
def mock_llm_config() -> LLMConfig:
    """Create a mock LLM configuration."""
    from pydantic import SecretStr

    return LLMConfig(
        provider=LLMProvider.ANTHROPIC,
        api_key=SecretStr("test-api-key"),
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        temperature=0.7,
    )


@pytest.fixture
def mock_mimir_config(monkeypatch: pytest.MonkeyPatch) -> MimirConfig:
    """Create a mock Mímir configuration."""
    # Set environment variables
    monkeypatch.setenv("MIMIR_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("MIMIR_LLM_API_KEY", "test-api-key")
    monkeypatch.setenv("MIMIR_LLM_MODEL", "claude-sonnet-4-20250514")
    monkeypatch.setenv("MIMIR_TELEGRAM_OWNER_ID", "123456789")
    monkeypatch.setenv("MIMIR_OPERATING_MODE", "normal")

    return MimirConfig()


class MockLLMProvider(LLMProviderBase):
    """Mock LLM provider for testing."""

    def __init__(self, responses: list[Response] | None = None) -> None:
        """Initialize with optional preset responses."""
        self._responses = responses or []
        self._response_index = 0
        self._calls: list[dict[str, Any]] = []

    @property
    def name(self) -> str:
        return "mock"

    @property
    def model(self) -> str:
        return "mock-model"

    async def complete(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> Response:
        self._calls.append(
            {
                "messages": messages,
                "tools": tools,
                "system": system,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        )

        if self._responses and self._response_index < len(self._responses):
            response = self._responses[self._response_index]
            self._response_index += 1
            return response

        # Default response
        return Response(
            content="Mock response",
            tool_calls=None,
            stop_reason=StopReason.END_TURN,
            usage=Usage(input_tokens=10, output_tokens=20),
            model="mock-model",
        )

    async def stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AsyncIterator[ResponseChunk]:
        response = await self.complete(messages, tools, system, max_tokens, temperature)
        yield ResponseChunk(delta_content=response.content)
        yield ResponseChunk(is_final=True, response=response)

    @property
    def calls(self) -> list[dict[str, Any]]:
        """Get recorded calls."""
        return self._calls


@pytest.fixture
def mock_llm_provider() -> MockLLMProvider:
    """Create a mock LLM provider."""
    return MockLLMProvider()


class MockTool(BaseTool):
    """Mock tool for testing."""

    def __init__(
        self,
        name: str = "mock_tool",
        description: str = "A mock tool for testing",
        result: str = "Mock result",
    ) -> None:
        self._name = name
        self._description = description
        self._result = result
        self._calls: list[dict[str, Any]] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Test query"},
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs: Any) -> str:
        self._calls.append(kwargs)
        return self._result

    @property
    def calls(self) -> list[dict[str, Any]]:
        """Get recorded calls."""
        return self._calls


@pytest.fixture
def mock_tool() -> MockTool:
    """Create a mock tool."""
    return MockTool()


@pytest.fixture
def tool_registry(mock_tool: MockTool) -> ToolRegistry:
    """Create a tool registry with a mock tool."""
    registry = ToolRegistry()
    registry.register(mock_tool)
    return registry


@pytest.fixture
def sample_message() -> Message:
    """Create a sample user message."""
    return Message.user("Hello, Mímir!")


@pytest.fixture
def sample_response() -> Response:
    """Create a sample LLM response."""
    return Response(
        content="Hello! How can I help you with Home Assistant today?",
        tool_calls=None,
        stop_reason=StopReason.END_TURN,
        usage=Usage(input_tokens=10, output_tokens=15),
        model="claude-sonnet-4-20250514",
    )
