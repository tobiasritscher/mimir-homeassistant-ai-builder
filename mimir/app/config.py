"""Configuration management for Mímir."""

from __future__ import annotations

import json
import os
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    AZURE = "azure"
    OLLAMA = "ollama"
    VLLM = "vllm"


class OperatingMode(str, Enum):
    """Agent operating modes."""

    CHAT = "chat"  # Read-only
    NORMAL = "normal"  # With confirmations
    YOLO = "yolo"  # Auto-approve all


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: LLMProvider = LLMProvider.ANTHROPIC
    api_key: SecretStr
    model: str = "claude-sonnet-4-20250514"
    base_url: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.7


class TelegramConfig(BaseModel):
    """Telegram configuration."""

    owner_id: int


class GitConfig(BaseModel):
    """Git configuration."""

    enabled: bool = True
    author_name: str = "Mímir"
    author_email: str = "mimir@asgard.local"
    branch: str = "mimir-changes"


class SafetyConfig(BaseModel):
    """Safety and rate limiting configuration."""

    deletions_per_hour: int = 5
    modifications_per_hour: int = 20
    yolo_mode_duration_minutes: int = 10


class MimirConfig(BaseSettings):
    """Main configuration for Mímir.

    Configuration is loaded from:
    1. /data/options.json (HA add-on config)
    2. Environment variables with MIMIR_ prefix
    """

    model_config = SettingsConfigDict(
        env_prefix="MIMIR_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # LLM settings
    llm_provider: LLMProvider = LLMProvider.ANTHROPIC
    llm_api_key: SecretStr = Field(default=SecretStr(""))
    llm_model: str = "claude-sonnet-4-20250514"
    llm_base_url: str | None = None

    # Telegram settings
    telegram_owner_id: int = 0

    # Operating mode
    operating_mode: OperatingMode = OperatingMode.NORMAL

    # Safety settings
    yolo_mode_duration_minutes: int = 10
    deletions_per_hour: int = 5
    modifications_per_hour: int = 20

    # Git settings
    git_enabled: bool = True
    git_author_name: str = "Mímir"
    git_author_email: str = "mimir@asgard.local"

    # Debug
    debug: bool = False

    # Supervisor token (injected by HA)
    supervisor_token: SecretStr | None = None

    @field_validator("telegram_owner_id")
    @classmethod
    def validate_telegram_owner_id(cls, v: int) -> int:
        """Validate Telegram owner ID is set."""
        if v == 0:
            raise ValueError("telegram_owner_id must be configured")
        return v

    @property
    def llm(self) -> LLMConfig:
        """Get LLM configuration as a structured object."""
        return LLMConfig(
            provider=self.llm_provider,
            api_key=self.llm_api_key,
            model=self.llm_model,
            base_url=self.llm_base_url,
        )

    @property
    def telegram(self) -> TelegramConfig:
        """Get Telegram configuration as a structured object."""
        return TelegramConfig(owner_id=self.telegram_owner_id)

    @property
    def git(self) -> GitConfig:
        """Get Git configuration as a structured object."""
        return GitConfig(
            enabled=self.git_enabled,
            author_name=self.git_author_name,
            author_email=self.git_author_email,
        )

    @property
    def safety(self) -> SafetyConfig:
        """Get safety configuration as a structured object."""
        return SafetyConfig(
            deletions_per_hour=self.deletions_per_hour,
            modifications_per_hour=self.modifications_per_hour,
            yolo_mode_duration_minutes=self.yolo_mode_duration_minutes,
        )


def load_addon_options() -> dict[str, Any]:
    """Load options from HA add-on options.json.

    Returns:
        Dictionary of options, or empty dict if not running as add-on.
    """
    options_path = Path("/data/options.json")
    if options_path.exists():
        with open(options_path) as f:
            return json.load(f)
    return {}


def load_config() -> MimirConfig:
    """Load configuration from all sources.

    Priority (highest to lowest):
    1. Environment variables
    2. /data/options.json (HA add-on)
    3. Defaults

    Returns:
        Validated MimirConfig instance.
    """
    # Load add-on options first
    addon_options = load_addon_options()

    # Map add-on options to environment variables if not already set
    option_to_env = {
        "llm_provider": "MIMIR_LLM_PROVIDER",
        "llm_api_key": "MIMIR_LLM_API_KEY",
        "llm_model": "MIMIR_LLM_MODEL",
        "llm_base_url": "MIMIR_LLM_BASE_URL",
        "telegram_owner_id": "MIMIR_TELEGRAM_OWNER_ID",
        "operating_mode": "MIMIR_OPERATING_MODE",
        "yolo_mode_duration_minutes": "MIMIR_YOLO_MODE_DURATION_MINUTES",
        "deletions_per_hour": "MIMIR_DELETIONS_PER_HOUR",
        "modifications_per_hour": "MIMIR_MODIFICATIONS_PER_HOUR",
        "git_enabled": "MIMIR_GIT_ENABLED",
        "git_author_name": "MIMIR_GIT_AUTHOR_NAME",
        "git_author_email": "MIMIR_GIT_AUTHOR_EMAIL",
        "debug": "MIMIR_DEBUG",
    }

    for option_key, env_key in option_to_env.items():
        if option_key in addon_options and env_key not in os.environ:
            value = addon_options[option_key]
            if isinstance(value, bool):
                value = str(value).lower()
            os.environ[env_key] = str(value)

    # Get supervisor token
    supervisor_token = os.environ.get("SUPERVISOR_TOKEN")
    if supervisor_token:
        os.environ["MIMIR_SUPERVISOR_TOKEN"] = supervisor_token

    return MimirConfig()
