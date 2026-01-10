"""Web interface module for Mímir."""

from .handlers import setup_routes
from .templates import AUDIT_HTML, GIT_HTML, STATUS_HTML

__all__ = ["AUDIT_HTML", "GIT_HTML", "STATUS_HTML", "setup_routes"]
