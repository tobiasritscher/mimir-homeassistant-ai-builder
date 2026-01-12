"""Local LLM providers (Ollama, vLLM) using OpenAI-compatible API."""

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


class OllamaProvider(LLMProvider):
    """Ollama LLM provider using OpenAI-compatible API."""

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434/v1",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> None:
        """Initialize the Ollama provider.

        Args:
            model: Model to use (e.g., llama3.2, mistral, codellama).
            base_url: Ollama API URL. Default is localhost.
            max_tokens: Default max tokens.
            temperature: Default temperature.
        """
        # Ollama doesn't need an API key
        self._client = AsyncOpenAI(api_key="ollama", base_url=base_url)
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

    @property
    def name(self) -> str:
        """Return the provider name."""
        return "ollama"

    @property
    def model(self) -> str:
        """Return the current model name."""
        return self._model

    def _convert_messages(
        self, messages: list[Message], system: str | None = None
    ) -> list[dict[str, Any]]:
        """Convert internal messages to OpenAI format."""
        result: list[dict[str, Any]] = []

        if system:
            result.append({"role": "system", "content": system})

        for msg in messages:
            if msg.role == Role.USER:
                if isinstance(msg.content, str):
                    result.append({"role": "user", "content": msg.content})
                else:
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

                if msg.content and isinstance(msg.content, str):
                    assistant_msg["content"] = msg.content
                else:
                    assistant_msg["content"] = None

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
        """Parse response to internal format."""
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

        finish_reason_map = {
            "stop": StopReason.END_TURN,
            "tool_calls": StopReason.TOOL_USE,
            "length": StopReason.MAX_TOKENS,
        }
        stop_reason = finish_reason_map.get(choice.finish_reason, StopReason.END_TURN)

        usage = Usage(input_tokens=0, output_tokens=0)
        if hasattr(response, "usage") and response.usage:
            usage = Usage(
                input_tokens=response.usage.prompt_tokens or 0,
                output_tokens=response.usage.completion_tokens or 0,
            )

        return Response(
            content=content,
            tool_calls=tool_calls if tool_calls else None,
            stop_reason=stop_reason,
            usage=usage,
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
        """Send a completion request to Ollama."""
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

        logger.debug("Sending request to Ollama: %d messages", len(messages))

        response = await self._client.chat.completions.create(**kwargs)

        logger.debug("Received response from Ollama")

        return self._parse_response(response)

    async def stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AsyncGenerator[ResponseChunk, None]:
        """Stream a completion response from Ollama."""
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

        logger.debug("Starting stream from Ollama: %d messages", len(messages))

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

            if delta.content:
                accumulated_content += delta.content
                yield ResponseChunk(delta_content=delta.content)

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

        finish_reason_map = {
            "stop": StopReason.END_TURN,
            "tool_calls": StopReason.TOOL_USE,
            "length": StopReason.MAX_TOKENS,
        }
        stop_reason = finish_reason_map.get(finish_reason or "stop", StopReason.END_TURN)

        yield ResponseChunk(
            is_final=True,
            response=Response(
                content=accumulated_content if accumulated_content else None,
                tool_calls=tool_calls if tool_calls else None,
                stop_reason=stop_reason,
                usage=Usage(input_tokens=0, output_tokens=0),
                model=model_name,
            ),
        )

    async def close(self) -> None:
        """Close the Ollama client."""
        await self._client.close()


class VLLMProvider(LLMProvider):
    """vLLM LLM provider using OpenAI-compatible API."""

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:8000/v1",
        api_key: str = "EMPTY",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> None:
        """Initialize the vLLM provider.

        Args:
            model: Model to use (must match the model served by vLLM).
            base_url: vLLM API URL. Default is localhost:8000.
            api_key: API key (vLLM doesn't require one by default).
            max_tokens: Default max tokens.
            temperature: Default temperature.
        """
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

    @property
    def name(self) -> str:
        """Return the provider name."""
        return "vllm"

    @property
    def model(self) -> str:
        """Return the current model name."""
        return self._model

    def _convert_messages(
        self, messages: list[Message], system: str | None = None
    ) -> list[dict[str, Any]]:
        """Convert internal messages to OpenAI format."""
        result: list[dict[str, Any]] = []

        if system:
            result.append({"role": "system", "content": system})

        for msg in messages:
            if msg.role == Role.USER:
                if isinstance(msg.content, str):
                    result.append({"role": "user", "content": msg.content})
                else:
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

                if msg.content and isinstance(msg.content, str):
                    assistant_msg["content"] = msg.content
                else:
                    assistant_msg["content"] = None

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
        """Parse response to internal format."""
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

        finish_reason_map = {
            "stop": StopReason.END_TURN,
            "tool_calls": StopReason.TOOL_USE,
            "length": StopReason.MAX_TOKENS,
        }
        stop_reason = finish_reason_map.get(choice.finish_reason, StopReason.END_TURN)

        usage = Usage(input_tokens=0, output_tokens=0)
        if hasattr(response, "usage") and response.usage:
            usage = Usage(
                input_tokens=response.usage.prompt_tokens or 0,
                output_tokens=response.usage.completion_tokens or 0,
            )

        return Response(
            content=content,
            tool_calls=tool_calls if tool_calls else None,
            stop_reason=stop_reason,
            usage=usage,
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
        """Send a completion request to vLLM."""
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

        logger.debug("Sending request to vLLM: %d messages", len(messages))

        response = await self._client.chat.completions.create(**kwargs)

        logger.debug("Received response from vLLM")

        return self._parse_response(response)

    async def stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AsyncGenerator[ResponseChunk, None]:
        """Stream a completion response from vLLM."""
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

        logger.debug("Starting stream from vLLM: %d messages", len(messages))

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

            if delta.content:
                accumulated_content += delta.content
                yield ResponseChunk(delta_content=delta.content)

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

        finish_reason_map = {
            "stop": StopReason.END_TURN,
            "tool_calls": StopReason.TOOL_USE,
            "length": StopReason.MAX_TOKENS,
        }
        stop_reason = finish_reason_map.get(finish_reason or "stop", StopReason.END_TURN)

        yield ResponseChunk(
            is_final=True,
            response=Response(
                content=accumulated_content if accumulated_content else None,
                tool_calls=tool_calls if tool_calls else None,
                stop_reason=stop_reason,
                usage=Usage(input_tokens=0, output_tokens=0),
                model=model_name,
            ),
        )

    async def close(self) -> None:
        """Close the vLLM client."""
        await self._client.close()
