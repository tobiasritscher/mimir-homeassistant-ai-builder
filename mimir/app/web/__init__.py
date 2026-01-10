"""Web interface module for Mímir."""

from .handlers import request_logger_middleware, setup_routes
from .templates import AUDIT_HTML, CHAT_HTML, GIT_HTML, STATUS_HTML

__all__ = [
    "AUDIT_HTML",
    "CHAT_HTML",
    "GIT_HTML",
    "STATUS_HTML",
    "request_logger_middleware",
    "setup_routes",
]
