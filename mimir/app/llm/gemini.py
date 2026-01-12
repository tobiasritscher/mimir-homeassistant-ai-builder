"""Google Gemini LLM provider implementation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

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


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-pro",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> None:
        """Initialize the Gemini provider.

        Args:
            api_key: Google AI API key.
            model: Model to use (e.g., gemini-1.5-pro, gemini-1.5-flash).
            max_tokens: Default max tokens.
            temperature: Default temperature.
        """
        genai.configure(api_key=api_key)
        self._model_name = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._model = genai.GenerativeModel(model)

    @property
    def name(self) -> str:
        """Return the provider name."""
        return "gemini"

    @property
    def model(self) -> str:
        """Return the current model name."""
        return self._model_name

    def _convert_messages(
        self, messages: list[Message], system: str | None = None
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Convert internal messages to Gemini format.

        Returns:
            Tuple of (messages, system_instruction).
        """
        result: list[dict[str, Any]] = []

        for msg in messages:
            if msg.role == Role.USER:
                if isinstance(msg.content, str):
                    result.append({"role": "user", "parts": [msg.content]})
                else:
                    # Handle tool results
                    parts = []
                    for block in msg.content:
                        if block.type == "tool_result" and block.tool_result:
                            parts.append(
                                {
                                    "function_response": {
                                        "name": block.tool_result.tool_call_id,
                                        "response": {"result": block.tool_result.content},
                                    }
                                }
                            )
                    if parts:
                        result.append({"role": "user", "parts": parts})

            elif msg.role == Role.ASSISTANT:
                parts = []

                # Add content if present
                if msg.content and isinstance(msg.content, str):
                    parts.append(msg.content)

                # Add tool calls if present
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        parts.append(
                            {
                                "function_call": {
                                    "name": tc.name,
                                    "args": tc.arguments,
                                }
                            }
                        )

                if parts:
                    result.append({"role": "model", "parts": parts})

        return result, system

    def _convert_tools(self, tools: list[Tool]) -> list[dict[str, Any]]:
        """Convert internal tools to Gemini function declarations."""
        declarations = []
        for tool in tools:
            declaration = {
                "name": tool.name,
                "description": tool.description,
            }
            if tool.parameters:
                declaration["parameters"] = tool.parameters
            declarations.append(declaration)

        return [{"function_declarations": declarations}]

    def _parse_response(self, response: Any) -> Response:
        """Parse Gemini response to internal format."""
        candidate = response.candidates[0]
        content_parts = candidate.content.parts

        content = None
        tool_calls = []

        for part in content_parts:
            if hasattr(part, "text") and part.text:
                content = (content or "") + part.text
            elif hasattr(part, "function_call"):
                fc = part.function_call
                tool_calls.append(
                    ToolCall(
                        id=fc.name,  # Gemini uses function name as ID
                        name=fc.name,
                        arguments=dict(fc.args),
                    )
                )

        # Map finish reason
        finish_reason = candidate.finish_reason
        if tool_calls:
            stop_reason = StopReason.TOOL_USE
        elif finish_reason == 1:  # STOP
            stop_reason = StopReason.END_TURN
        elif finish_reason == 2:  # MAX_TOKENS
            stop_reason = StopReason.MAX_TOKENS
        else:
            stop_reason = StopReason.END_TURN

        # Get usage if available
        usage_metadata = getattr(response, "usage_metadata", None)
        if usage_metadata:
            usage = Usage(
                input_tokens=usage_metadata.prompt_token_count,
                output_tokens=usage_metadata.candidates_token_count,
            )
        else:
            usage = Usage(input_tokens=0, output_tokens=0)

        return Response(
            content=content,
            tool_calls=tool_calls if tool_calls else None,
            stop_reason=stop_reason,
            usage=usage,
            model=self._model_name,
        )

    async def complete(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> Response:
        """Send a completion request to Gemini."""
        gemini_messages, system_instruction = self._convert_messages(messages, system)

        generation_config = GenerationConfig(
            max_output_tokens=max_tokens or self._max_tokens,
            temperature=temperature if temperature is not None else self._temperature,
        )

        # Create model with system instruction if provided
        if system_instruction:
            model = genai.GenerativeModel(
                self._model_name,
                system_instruction=system_instruction,
            )
        else:
            model = self._model

        kwargs: dict[str, Any] = {
            "generation_config": generation_config,
        }

        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        logger.debug("Sending request to Gemini: %d messages", len(messages))

        # Convert messages to chat history format
        chat = model.start_chat(history=gemini_messages[:-1] if gemini_messages else [])

        # Get the last message to send
        if gemini_messages:
            last_message = gemini_messages[-1]
            last_content = last_message.get("parts", [""])
            response = await chat.send_message_async(last_content, **kwargs)
        else:
            response = await chat.send_message_async("Hello", **kwargs)

        logger.debug("Received response from Gemini")

        return self._parse_response(response)

    async def stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AsyncGenerator[ResponseChunk, None]:
        """Stream a completion response from Gemini."""
        gemini_messages, system_instruction = self._convert_messages(messages, system)

        generation_config = GenerationConfig(
            max_output_tokens=max_tokens or self._max_tokens,
            temperature=temperature if temperature is not None else self._temperature,
        )

        # Create model with system instruction if provided
        if system_instruction:
            model = genai.GenerativeModel(
                self._model_name,
                system_instruction=system_instruction,
            )
        else:
            model = self._model

        kwargs: dict[str, Any] = {
            "generation_config": generation_config,
            "stream": True,
        }

        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        logger.debug("Starting stream from Gemini: %d messages", len(messages))

        # Convert messages to chat history format
        chat = model.start_chat(history=gemini_messages[:-1] if gemini_messages else [])

        # Get the last message to send
        if gemini_messages:
            last_message = gemini_messages[-1]
            last_content = last_message.get("parts", [""])
        else:
            last_content = "Hello"

        accumulated_content = ""
        tool_calls: list[ToolCall] = []

        async for chunk in await chat.send_message_async(last_content, **kwargs):
            if chunk.text:
                accumulated_content += chunk.text
                yield ResponseChunk(delta_content=chunk.text)

            # Check for function calls in the chunk
            for part in chunk.parts:
                if hasattr(part, "function_call"):
                    fc = part.function_call
                    tool_call = ToolCall(
                        id=fc.name,
                        name=fc.name,
                        arguments=dict(fc.args),
                    )
                    tool_calls.append(tool_call)
                    yield ResponseChunk(delta_tool_call=tool_call)

        # Determine stop reason
        if tool_calls:
            stop_reason = StopReason.TOOL_USE
        else:
            stop_reason = StopReason.END_TURN

        # Yield final response
        yield ResponseChunk(
            is_final=True,
            response=Response(
                content=accumulated_content if accumulated_content else None,
                tool_calls=tool_calls if tool_calls else None,
                stop_reason=stop_reason,
                usage=Usage(input_tokens=0, output_tokens=0),
                model=self._model_name,
            ),
        )

    async def close(self) -> None:
        """Close the Gemini client."""
        # No cleanup needed for Gemini
        pass
