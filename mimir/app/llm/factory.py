"""Factory for creating LLM providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..config import LLMConfig
from ..config import LLMProvider as LLMProviderEnum
from ..utils.logging import get_logger
from .anthropic import AnthropicProvider
from .openai import OpenAIProvider

if TYPE_CHECKING:
    from .base import LLMProvider

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
            return OpenAIProvider(
                api_key=config.api_key.get_secret_value(),
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                base_url=config.base_url,
            )

        case LLMProviderEnum.GEMINI:
            from .gemini import GeminiProvider

            return GeminiProvider(
                api_key=config.api_key.get_secret_value(),
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )

        case LLMProviderEnum.AZURE:
            # Azure uses the OpenAI provider with a custom base URL
            if not config.base_url:
                raise UnsupportedProviderError(
                    "Azure provider requires base_url to be set to your Azure OpenAI endpoint."
                )
            return OpenAIProvider(
                api_key=config.api_key.get_secret_value(),
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                base_url=config.base_url,
            )

        case LLMProviderEnum.OLLAMA:
            from .local import OllamaProvider

            # Default to localhost if no base_url provided
            base_url = config.base_url or "http://localhost:11434/v1"
            return OllamaProvider(
                model=config.model,
                base_url=base_url,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )

        case LLMProviderEnum.VLLM:
            from .local import VLLMProvider

            # Default to localhost if no base_url provided
            base_url = config.base_url or "http://localhost:8000/v1"
            return VLLMProvider(
                model=config.model,
                base_url=base_url,
                api_key=config.api_key.get_secret_value() if config.api_key else "EMPTY",
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )

        case _:
            raise UnsupportedProviderError(f"Unknown provider: {config.provider}")
