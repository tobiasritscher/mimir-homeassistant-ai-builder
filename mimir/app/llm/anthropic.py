"""Anthropic Claude LLM provider implementation."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from anthropic import AsyncAnthropic

from ..utils.logging import get_logger
from .base import LLMProvider
from .types import (
    ContentBlock,
    Message,
    Response,
    ResponseChunk,
    Role,
    StopReason,
    Tool,
    ToolCall,
    ToolResult,
    Usage,
)

logger = get_logger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> None:
        """Initialize the Anthropic provider.

        Args:
            api_key: Anthropic API key.
            model: Model to use.
            max_tokens: Default max tokens.
            temperature: Default temperature.
        """
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

    @property
    def name(self) -> str:
        """Return the provider name."""
        return "anthropic"

    @property
    def model(self) -> str:
        """Return the current model name."""
        return self._model

    def _convert_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Convert internal messages to Anthropic format."""
        result = []

        for msg in messages:
            if msg.role == Role.USER:
                if isinstance(msg.content, str):
                    result.append({"role": "user", "content": msg.content})
                else:
                    # Handle tool results
                    content_blocks = []
                    for block in msg.content:
                        if block.type == "tool_result" and block.tool_result:
                            content_blocks.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.tool_result.tool_call_id,
                                    "content": block.tool_result.content,
                                    "is_error": block.tool_result.is_error,
                                }
                            )
                    result.append({"role": "user", "content": content_blocks})

            elif msg.role == Role.ASSISTANT:
                content_blocks: list[dict[str, Any]] = []

                # Add text content if present
                if msg.content and isinstance(msg.content, str):
                    content_blocks.append({"type": "text", "text": msg.content})

                # Add tool use blocks
                if msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        content_blocks.append(
                            {
                                "type": "tool_use",
                                "id": tool_call.id,
                                "name": tool_call.name,
                                "input": tool_call.arguments,
                            }
                        )

                result.append({"role": "assistant", "content": content_blocks})

        return result

    def _convert_tools(self, tools: list[Tool]) -> list[dict[str, Any]]:
        """Convert internal tools to Anthropic format."""
        return [tool.to_anthropic_format() for tool in tools]

    def _parse_response(self, response: Any) -> Response:
        """Parse Anthropic response to internal format."""
        content = None
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input,
                    )
                )

        # Map stop reason
        stop_reason_map = {
            "end_turn": StopReason.END_TURN,
            "tool_use": StopReason.TOOL_USE,
            "max_tokens": StopReason.MAX_TOKENS,
            "stop_sequence": StopReason.STOP_SEQUENCE,
        }
        stop_reason = stop_reason_map.get(response.stop_reason, StopReason.END_TURN)

        return Response(
            content=content,
            tool_calls=tool_calls if tool_calls else None,
            stop_reason=stop_reason,
            usage=Usage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            ),
            model=response.model,
        )

    async def complete(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> Response:
        """Send a completion request to Claude."""
        anthropic_messages = self._convert_messages(messages)

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens or self._max_tokens,
        }

        if temperature is not None:
            kwargs["temperature"] = temperature

        if system:
            kwargs["system"] = system

        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        logger.debug("Sending request to Anthropic: %d messages", len(messages))

        response = await self._client.messages.create(**kwargs)

        logger.debug(
            "Received response: %s, tokens: %d/%d",
            response.stop_reason,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )

        return self._parse_response(response)

    async def stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AsyncIterator[ResponseChunk]:
        """Stream a completion response from Claude."""
        anthropic_messages = self._convert_messages(messages)

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens or self._max_tokens,
        }

        if temperature is not None:
            kwargs["temperature"] = temperature

        if system:
            kwargs["system"] = system

        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        logger.debug("Starting stream from Anthropic: %d messages", len(messages))

        async with self._client.messages.stream(**kwargs) as stream:
            current_tool_call: dict[str, Any] | None = None
            accumulated_json = ""

            async for event in stream:
                if event.type == "content_block_start":
                    if event.content_block.type == "tool_use":
                        current_tool_call = {
                            "id": event.content_block.id,
                            "name": event.content_block.name,
                        }
                        accumulated_json = ""

                elif event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        yield ResponseChunk(delta_content=event.delta.text)
                    elif event.delta.type == "input_json_delta":
                        accumulated_json += event.delta.partial_json

                elif event.type == "content_block_stop":
                    if current_tool_call:
                        try:
                            arguments = json.loads(accumulated_json) if accumulated_json else {}
                        except json.JSONDecodeError:
                            arguments = {}

                        yield ResponseChunk(
                            delta_tool_call=ToolCall(
                                id=current_tool_call["id"],
                                name=current_tool_call["name"],
                                arguments=arguments,
                            )
                        )
                        current_tool_call = None

                elif event.type == "message_stop":
                    final_message = await stream.get_final_message()
                    yield ResponseChunk(
                        is_final=True,
                        response=self._parse_response(final_message),
                    )

    async def close(self) -> None:
        """Close the Anthropic client."""
        await self._client.close()
