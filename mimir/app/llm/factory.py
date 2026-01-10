"""Factory for creating LLM providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..config import LLMConfig, LLMProvider as LLMProviderEnum
from ..utils.logging import get_logger
from .anthropic import AnthropicProvider
from .base import LLMProvider

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class UnsupportedProviderError(Exception):
    """Raised when an unsupported LLM provider is requested."""

    pass


def create_provider(config: LLMConfig) -> LLMProvider:
    """Create an LLM provider based on configuration.

    Args:
        config: LLM configuration.

    Returns:
        An initialized LLM provider.

    Raises:
        UnsupportedProviderError: If the provider is not yet implemented.
    """
    logger.info("Creating LLM provider: %s (model: %s)", config.provider.value, config.model)

    match config.provider:
        case LLMProviderEnum.ANTHROPIC:
            return AnthropicProvider(
                api_key=config.api_key.get_secret_value(),
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )

        case LLMProviderEnum.OPENAI:
            raise UnsupportedProviderError(
                "OpenAI provider is not yet implemented. Coming in Phase 6."
            )

        case LLMProviderEnum.GEMINI:
            raise UnsupportedProviderError(
                "Gemini provider is not yet implemented. Coming in Phase 6."
            )

        case LLMProviderEnum.AZURE:
            raise UnsupportedProviderError(
                "Azure provider is not yet implemented. Coming in Phase 6."
            )

        case LLMProviderEnum.OLLAMA:
            raise UnsupportedProviderError(
                "Ollama provider is not yet implemented. Coming in Phase 6."
            )

        case LLMProviderEnum.VLLM:
            raise UnsupportedProviderError(
                "vLLM provider is not yet implemented. Coming in Phase 6."
            )

        case _:
            raise UnsupportedProviderError(f"Unknown provider: {config.provider}")
