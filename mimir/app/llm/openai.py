"""OpenAI LLM provider implementation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from openai import AsyncOpenAI

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

from ..utils.logging import get_logger
from .base import LLMProvider
from .types import (
    Message,
    Response,
    ResponseChunk,
    Role,
    StopReason,
    Tool,
    ToolCall,
    Usage,
)

logger = get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI GPT LLM provider."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        base_url: str | None = None,
    ) -> None:
        """Initialize the OpenAI provider.

        Args:
            api_key: OpenAI API key.
            model: Model to use.
            max_tokens: Default max tokens.
            temperature: Default temperature.
            base_url: Optional base URL for API (for Azure or compatible APIs).
        """
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

    @property
    def name(self) -> str:
        """Return the provider name."""
        return "openai"

    @property
    def model(self) -> str:
        """Return the current model name."""
        return self._model

    def _convert_messages(
        self, messages: list[Message], system: str | None = None
    ) -> list[dict[str, Any]]:
        """Convert internal messages to OpenAI format."""
        result: list[dict[str, Any]] = []

        # Add system message first if provided
        if system:
            result.append({"role": "system", "content": system})

        for msg in messages:
            if msg.role == Role.USER:
                if isinstance(msg.content, str):
                    result.append({"role": "user", "content": msg.content})
                else:
                    # Handle tool results - OpenAI expects them as separate tool messages
                    for block in msg.content:
                        if block.type == "tool_result" and block.tool_result:
                            result.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": block.tool_result.tool_call_id,
                                    "content": block.tool_result.content,
                                }
                            )

            elif msg.role == Role.ASSISTANT:
                assistant_msg: dict[str, Any] = {"role": "assistant"}

                # Add content if present
                if msg.content and isinstance(msg.content, str):
                    assistant_msg["content"] = msg.content
                else:
                    assistant_msg["content"] = None

                # Add tool calls if present
                if msg.tool_calls:
                    assistant_msg["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                        for tc in msg.tool_calls
                    ]

                result.append(assistant_msg)

        return result

    def _convert_tools(self, tools: list[Tool]) -> list[dict[str, Any]]:
        """Convert internal tools to OpenAI format."""
        return [tool.to_openai_format() for tool in tools]

    def _parse_response(self, response: Any) -> Response:
        """Parse OpenAI response to internal format."""
        choice = response.choices[0]
        message = choice.message

        content = message.content
        tool_calls = []

        if message.tool_calls:
            for tc in message.tool_calls:
                try:
                    arguments = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=arguments,
                    )
                )

        # Map finish reason
        finish_reason_map = {
            "stop": StopReason.END_TURN,
            "tool_calls": StopReason.TOOL_USE,
            "length": StopReason.MAX_TOKENS,
        }
        stop_reason = finish_reason_map.get(choice.finish_reason, StopReason.END_TURN)

        return Response(
            content=content,
            tool_calls=tool_calls if tool_calls else None,
            stop_reason=stop_reason,
            usage=Usage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
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
        """Send a completion request to OpenAI."""
        openai_messages = self._convert_messages(messages, system)

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": openai_messages,
            "max_tokens": max_tokens or self._max_tokens,
        }

        if temperature is not None:
            kwargs["temperature"] = temperature
        else:
            kwargs["temperature"] = self._temperature

        if tools:
            kwargs["tools"] = self._convert_tools(tools)
            kwargs["tool_choice"] = "auto"

        logger.debug("Sending request to OpenAI: %d messages", len(messages))

        response = await self._client.chat.completions.create(**kwargs)

        logger.debug(
            "Received response: %s, tokens: %d/%d",
            response.choices[0].finish_reason,
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
        )

        return self._parse_response(response)

    async def stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AsyncGenerator[ResponseChunk, None]:
        """Stream a completion response from OpenAI."""
        openai_messages = self._convert_messages(messages, system)

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": openai_messages,
            "max_tokens": max_tokens or self._max_tokens,
            "stream": True,
        }

        if temperature is not None:
            kwargs["temperature"] = temperature
        else:
            kwargs["temperature"] = self._temperature

        if tools:
            kwargs["tools"] = self._convert_tools(tools)
            kwargs["tool_choice"] = "auto"

        logger.debug("Starting stream from OpenAI: %d messages", len(messages))

        # Track tool calls being accumulated
        current_tool_calls: dict[int, dict[str, Any]] = {}
        accumulated_content = ""
        finish_reason = None
        model_name = self._model

        async for chunk in await self._client.chat.completions.create(**kwargs):
            if chunk.model:
                model_name = chunk.model

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            chunk_finish_reason = chunk.choices[0].finish_reason

            if chunk_finish_reason:
                finish_reason = chunk_finish_reason

            # Handle content delta
            if delta.content:
                accumulated_content += delta.content
                yield ResponseChunk(delta_content=delta.content)

            # Handle tool call deltas
            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index

                    if idx not in current_tool_calls:
                        current_tool_calls[idx] = {
                            "id": tc_delta.id or "",
                            "name": "",
                            "arguments": "",
                        }

                    if tc_delta.id:
                        current_tool_calls[idx]["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            current_tool_calls[idx]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            current_tool_calls[idx]["arguments"] += tc_delta.function.arguments

        # Yield final tool calls
        tool_calls = []
        for idx in sorted(current_tool_calls.keys()):
            tc_data = current_tool_calls[idx]
            try:
                arguments = json.loads(tc_data["arguments"]) if tc_data["arguments"] else {}
            except json.JSONDecodeError:
                arguments = {}

            tool_call = ToolCall(
                id=tc_data["id"],
                name=tc_data["name"],
                arguments=arguments,
            )
            tool_calls.append(tool_call)
            yield ResponseChunk(delta_tool_call=tool_call)

        # Map finish reason
        finish_reason_map = {
            "stop": StopReason.END_TURN,
            "tool_calls": StopReason.TOOL_USE,
            "length": StopReason.MAX_TOKENS,
        }
        stop_reason = finish_reason_map.get(finish_reason or "stop", StopReason.END_TURN)

        # Yield final response
        yield ResponseChunk(
            is_final=True,
            response=Response(
                content=accumulated_content if accumulated_content else None,
                tool_calls=tool_calls if tool_calls else None,
                stop_reason=stop_reason,
                usage=Usage(input_tokens=0, output_tokens=0),  # Not available in streaming
                model=model_name,
            ),
        )

    async def close(self) -> None:
        """Close the OpenAI client."""
        await self._client.close()
