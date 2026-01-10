"""Logging configuration for Mímir."""

import logging
import os
import sys
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def setup_logging(level: LogLevel | None = None) -> logging.Logger:
    """Configure logging for Mímir.

    Args:
        level: Log level to use. If not specified, reads from LOG_LEVEL env var.

    Returns:
        The root logger for Mímir.
    """
    level_str: str = level if level is not None else os.environ.get("LOG_LEVEL", "INFO").upper()

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Create handler for stdout (Docker logs)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level_str))
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Create Mímir logger
    logger = logging.getLogger("mimir")
    logger.setLevel(getattr(logging, level_str))

    # Reduce noise from third-party libraries
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logger.debug("Logging configured with level: %s", level_str)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module.

    Args:
        name: Module name (typically __name__).

    Returns:
        Logger instance.
    """
    return logging.getLogger(f"mimir.{name}")
