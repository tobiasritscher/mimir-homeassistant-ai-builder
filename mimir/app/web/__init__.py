"""Web interface module for Mímir."""

from .handlers import normalize_path_middleware, request_logger_middleware, setup_routes
from .templates import AUDIT_HTML, CHAT_HTML, GIT_HTML, STATUS_HTML

__all__ = [
    "AUDIT_HTML",
    "CHAT_HTML",
    "GIT_HTML",
    "STATUS_HTML",
    "normalize_path_middleware",
    "request_logger_middleware",
    "setup_routes",
]
