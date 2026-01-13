"""HTTP request handlers for Mímir web interface."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from aiohttp import web

from ..ha.types import UserContext
from ..utils.logging import get_logger
from .templates import AUDIT_HTML, CHAT_HTML, GIT_HTML, STATUS_HTML

if TYPE_CHECKING:
    from ..db.repository import AuditRepository
    from ..git.manager import GitManager

logger = get_logger(__name__)

# Type alias for aiohttp handler
Handler = Callable[[web.Request], Awaitable[web.StreamResponse]]


def get_base_path(request: web.Request) -> str:
    """Extract the ingress base path from the request.

    Home Assistant's ingress proxy adds an X-Ingress-Path header that contains
    the base path (e.g., /api/hassio_ingress/abc123). We use this to construct
    absolute URLs for API calls in the frontend JavaScript.

    Returns:
        The ingress base path, or empty string if not behind ingress.
    """
    return request.headers.get("X-Ingress-Path", "")


def get_user_context(request: web.Request) -> UserContext:
    """Extract user context from Home Assistant ingress headers.

    When accessed through HA's ingress, these headers are automatically set:
    - X-Remote-User-Id: The HA user's unique ID
    - X-Remote-User-Name: The HA username (login name)
    - X-Remote-User-Display-Name: The user's display name

    Returns:
        UserContext with user information from headers, or defaults for non-ingress access.
    """
    return UserContext(
        user_id=request.headers.get("X-Remote-User-Id", "web_user"),
        username=request.headers.get("X-Remote-User-Name"),
        display_name=request.headers.get("X-Remote-User-Display-Name"),
        source="web",
    )


def add_route_with_trailing_slash(
    router: web.UrlDispatcher, method: str, path: str, handler: Handler
) -> None:
    """Add a route that handles both with and without trailing slash.

    This is more reliable than cloning requests, especially with ingress.
    """
    # Add the canonical path
    if method == "GET":
        router.add_get(path, handler)
    elif method == "POST":
        router.add_post(path, handler)

    # Add trailing slash variant (if not root)
    if path != "/" and not path.endswith("/"):
        if method == "GET":
            router.add_get(path + "/", handler)
        elif method == "POST":
            router.add_post(path + "/", handler)


@web.middleware
async def request_logger_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    """Log all incoming requests for debugging."""
    # Get ingress path header for debugging
    ingress_path = request.headers.get("X-Ingress-Path", "")
    # Use INFO level so it always shows in logs (helps debug ingress issues)
    logger.info(
        "HTTP %s %s (X-Ingress-Path: %s)",
        request.method,
        request.path,
        ingress_path or "none",
    )
    try:
        response = await handler(request)
        logger.info("HTTP %s %s -> %d", request.method, request.path, response.status)
        return response
    except web.HTTPException as e:
        logger.info("HTTP %s %s -> %d (exception)", request.method, request.path, e.status)
        raise


def setup_routes(app: web.Application) -> None:
    """Set up all web routes.

    Routes are registered both with and without trailing slashes to handle
    ingress path variations without relying on request cloning.

    Args:
        app: The aiohttp application.
    """
    router = app.router

    # Main pages (with trailing slash variants)
    # Chat is the default view - simplest for ingress and most useful for users
    add_route_with_trailing_slash(router, "GET", "/", handle_chat_page)
    # Also handle // explicitly for ingress double-slash issue
    router.add_get("//", handle_chat_page)
    add_route_with_trailing_slash(router, "GET", "/status", handle_status)
    add_route_with_trailing_slash(router, "GET", "/health", handle_health)
    add_route_with_trailing_slash(router, "GET", "/debug", handle_debug)
    add_route_with_trailing_slash(router, "GET", "/audit", handle_audit_page)
    add_route_with_trailing_slash(router, "GET", "/git", handle_git_page)

    # Chat API (with trailing slash variants)
    add_route_with_trailing_slash(router, "POST", "/api/chat", handle_chat_message)
    add_route_with_trailing_slash(router, "GET", "/api/chat/history", handle_chat_history)
    add_route_with_trailing_slash(router, "POST", "/api/chat/clear", handle_chat_clear)

    # Audit API (with trailing slash variants)
    add_route_with_trailing_slash(router, "GET", "/api/audit", handle_audit_list)
    router.add_get(
        "/api/audit/{id}", handle_audit_detail
    )  # Dynamic routes don't need slash variant

    # Git API (with trailing slash variants)
    add_route_with_trailing_slash(router, "GET", "/api/git/status", handle_git_status)
    add_route_with_trailing_slash(router, "GET", "/api/git/commits", handle_git_commits)
    router.add_get(
        "/api/git/diff/{sha}", handle_git_diff
    )  # Dynamic routes don't need slash variant
    add_route_with_trailing_slash(router, "POST", "/api/git/commit", handle_git_commit)
    add_route_with_trailing_slash(router, "POST", "/api/git/rollback", handle_git_rollback)
    add_route_with_trailing_slash(router, "GET", "/api/git/branches", handle_git_branches)
    add_route_with_trailing_slash(router, "POST", "/api/git/branches", handle_git_create_branch)
    add_route_with_trailing_slash(router, "POST", "/api/git/checkout", handle_git_checkout)


# ============== Main Pages ==============


async def handle_status(request: web.Request) -> web.Response:
    """Handle GET / - Main status page with chat."""
    agent = request.app.get("agent")

    if not agent:
        return web.Response(text="Agent not initialized", status=503)

    html = STATUS_HTML.format(
        base_path=get_base_path(request),
        version=agent.VERSION,
        llm_provider=agent._llm.name,
        llm_model=agent._llm.model,
        operating_mode=agent._config.operating_mode.value,
        ha_status="Connected" if agent._ha_connected else "Disconnected",
        ha_status_class="status-ok" if agent._ha_connected else "status-error",
        ws_status="Connected" if agent._ws_connected else "Disconnected",
        ws_status_class="status-ok" if agent._ws_connected else "status-error",
        tool_count=len(agent._tool_registry),
    )
    return web.Response(text=html, content_type="text/html")


async def handle_health(request: web.Request) -> web.Response:
    """Handle GET /health - Health check endpoint."""
    agent = request.app.get("agent")

    if not agent:
        return web.json_response({"status": "initializing"}, status=503)

    return web.json_response(
        {
            "status": "ok",
            "version": agent.VERSION,
            "ha_connected": agent._ha_connected,
            "ws_connected": agent._ws_connected,
        }
    )


async def handle_debug(request: web.Request) -> web.Response:
    """Handle GET /debug - Debug endpoint for diagnosing ingress issues."""
    agent = request.app.get("agent")
    version = agent.VERSION if agent else "unknown"

    # Extract user context
    user = get_user_context(request)

    # Collect request info
    headers_info = "\n".join(f"  {k}: {v}" for k, v in request.headers.items())

    debug_text = f"""MIMIR DEBUG PAGE
================
Version: {version}
Path: {request.path}
Method: {request.method}
Host: {request.host}
Remote: {request.remote}

User Context (from HA ingress headers):
  User ID: {user.user_id}
  Username: {user.username or "(not set)"}
  Display Name: {user.display_name or "(not set)"}
  Friendly Name: {user.friendly_name}
  Source: {user.source}

All Headers:
{headers_info}

If you see this, the web server is working!
The ingress proxy is reaching Mímir successfully.
"""
    return web.Response(text=debug_text, content_type="text/plain")


async def handle_audit_page(request: web.Request) -> web.Response:
    """Handle GET /audit - Audit log page."""
    # Call .format() to convert doubled braces {{}} to single braces {}
    # and inject base_path for API URLs
    html = AUDIT_HTML.format(base_path=get_base_path(request))
    return web.Response(text=html, content_type="text/html")


async def handle_git_page(request: web.Request) -> web.Response:
    """Handle GET /git - Git history page."""
    # Call .format() to convert doubled braces {{}} to single braces {}
    # and inject base_path for API URLs
    html = GIT_HTML.format(base_path=get_base_path(request))
    return web.Response(text=html, content_type="text/html")


async def handle_chat_page(request: web.Request) -> web.Response:
    """Handle GET / or /chat - Chat page (default view for ingress)."""
    logger.info("Serving chat page for path: %s", request.path)
    # Call .format() to convert doubled braces {{}} to single braces {}
    # and inject base_path for API URLs
    html = CHAT_HTML.format(base_path=get_base_path(request))
    return web.Response(text=html, content_type="text/html")


# ============== Chat API ==============


async def handle_chat_message(request: web.Request) -> web.Response:
    """Handle POST /api/chat - Send a chat message."""
    agent = request.app.get("agent")

    if not agent or not agent._conversation_manager:
        return web.json_response(
            {"error": "Agent not ready"},
            status=503,
        )

    try:
        data = await request.json()
        message = data.get("message", "").strip()

        if not message:
            return web.json_response(
                {"error": "Message is required"},
                status=400,
            )

        # Extract user context from HA ingress headers
        user_context = get_user_context(request)
        logger.info(
            "Chat message from user: %s (%s)",
            user_context.friendly_name,
            user_context.user_id,
        )

        # Process the message with user context
        response = await agent._conversation_manager.process_message(
            message,
            user_context=user_context,
        )

        return web.json_response({"response": response})

    except Exception as e:
        logger.exception("Chat error: %s", e)
        return web.json_response(
            {"error": str(e)},
            status=500,
        )


async def handle_chat_history(request: web.Request) -> web.Response:
    """Handle GET /api/chat/history - Get conversation history for current user."""
    agent = request.app.get("agent")

    if not agent or not agent._conversation_manager:
        return web.json_response({"history": []})

    # Get user context to filter history by user
    user_context = get_user_context(request)

    # Load history from audit if not already in memory
    await agent._conversation_manager.load_history_from_audit(user_id=user_context.user_id)

    history = agent._conversation_manager.get_history(user_id=user_context.user_id)
    return web.json_response({"history": history})


async def handle_chat_clear(request: web.Request) -> web.Response:
    """Handle POST /api/chat/clear - Clear conversation history for current user."""
    agent = request.app.get("agent")

    if agent and agent._conversation_manager:
        # Get user context to clear only this user's history
        user_context = get_user_context(request)
        agent._conversation_manager.clear_history(user_id=user_context.user_id)

    return web.json_response({"status": "ok"})


# ============== Audit API ==============


async def handle_audit_list(request: web.Request) -> web.Response:
    """Handle GET /api/audit - List audit logs."""
    audit: AuditRepository | None = request.app.get("audit")

    if not audit:
        return web.json_response({"logs": [], "error": "Audit not enabled"})

    try:
        # Parse query parameters
        limit = int(request.query.get("limit", "50"))
        offset = int(request.query.get("offset", "0"))
        source = request.query.get("source")
        message_type = request.query.get("type")
        search = request.query.get("search")

        if search:
            logs = await audit.search_logs(search, limit=limit, offset=offset)
        else:
            logs = await audit.get_recent_logs(
                limit=limit,
                offset=offset,
                source=source,
                message_type=message_type,
            )

        return web.json_response({"logs": [log.to_dict() for log in logs]})

    except Exception as e:
        logger.exception("Audit list error: %s", e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_audit_detail(request: web.Request) -> web.Response:
    """Handle GET /api/audit/{id} - Get audit log detail."""
    audit: AuditRepository | None = request.app.get("audit")

    if not audit:
        return web.json_response({"error": "Audit not enabled"}, status=503)

    try:
        log_id = int(request.match_info["id"])
        log = await audit.get_log_by_id(log_id)

        if not log:
            return web.json_response({"error": "Log not found"}, status=404)

        return web.json_response(log.to_dict())

    except ValueError:
        return web.json_response({"error": "Invalid ID"}, status=400)
    except Exception as e:
        logger.exception("Audit detail error: %s", e)
        return web.json_response({"error": str(e)}, status=500)


# ============== Git API ==============


async def handle_git_status(request: web.Request) -> web.Response:
    """Handle GET /api/git/status - Get git status."""
    git: GitManager | None = request.app.get("git")

    if not git:
        return web.json_response({"error": "Git not enabled"}, status=503)

    try:
        status = await git.get_status()
        return web.json_response(status)
    except Exception as e:
        logger.exception("Git status error: %s", e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_git_commits(request: web.Request) -> web.Response:
    """Handle GET /api/git/commits - List commits."""
    git: GitManager | None = request.app.get("git")

    if not git:
        return web.json_response({"error": "Git not enabled"}, status=503)

    try:
        limit = int(request.query.get("limit", "20"))
        commits = await git.get_commits(limit=limit)
        return web.json_response({"commits": commits})
    except Exception as e:
        logger.exception("Git commits error: %s", e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_git_diff(request: web.Request) -> web.Response:
    """Handle GET /api/git/diff/{sha} - Get diff for a commit."""
    git: GitManager | None = request.app.get("git")

    if not git:
        return web.json_response({"error": "Git not enabled"}, status=503)

    try:
        sha = request.match_info["sha"]
        diff = await git.get_diff(sha)
        return web.json_response({"diff": diff})
    except Exception as e:
        logger.exception("Git diff error: %s", e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_git_commit(request: web.Request) -> web.Response:
    """Handle POST /api/git/commit - Commit all changes with auto-generated message."""
    git: GitManager | None = request.app.get("git")

    if not git:
        return web.json_response({"error": "Git not enabled"}, status=503)

    try:
        result = await git.commit_all()

        if result.get("status") == "no_changes":
            return web.json_response({"status": "no_changes", "message": "No changes to commit"})

        if result.get("status") == "error":
            return web.json_response({"error": result.get("error", "Commit failed")}, status=500)

        return web.json_response(
            {
                "status": "ok",
                "message": result.get("message", ""),
                "commit": result.get("commit", {}),
            }
        )
    except Exception as e:
        logger.exception("Git commit error: %s", e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_git_rollback(request: web.Request) -> web.Response:
    """Handle POST /api/git/rollback - Rollback to a commit."""
    git: GitManager | None = request.app.get("git")

    if not git:
        return web.json_response({"error": "Git not enabled"}, status=503)

    try:
        data = await request.json()
        sha = data.get("sha")

        if not sha:
            return web.json_response({"error": "SHA is required"}, status=400)

        await git.rollback(sha)
        return web.json_response({"status": "ok"})
    except Exception as e:
        logger.exception("Git rollback error: %s", e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_git_branches(request: web.Request) -> web.Response:
    """Handle GET /api/git/branches - List branches."""
    git: GitManager | None = request.app.get("git")

    if not git:
        return web.json_response({"error": "Git not enabled"}, status=503)

    try:
        branches = await git.get_branches()
        return web.json_response({"branches": branches})
    except Exception as e:
        logger.exception("Git branches error: %s", e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_git_create_branch(request: web.Request) -> web.Response:
    """Handle POST /api/git/branches - Create a branch."""
    git: GitManager | None = request.app.get("git")

    if not git:
        return web.json_response({"error": "Git not enabled"}, status=503)

    try:
        data = await request.json()
        name = data.get("name")

        if not name:
            return web.json_response({"error": "Branch name is required"}, status=400)

        await git.create_branch(name)
        return web.json_response({"status": "ok"})
    except Exception as e:
        logger.exception("Git create branch error: %s", e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_git_checkout(request: web.Request) -> web.Response:
    """Handle POST /api/git/checkout - Switch branch."""
    git: GitManager | None = request.app.get("git")

    if not git:
        return web.json_response({"error": "Git not enabled"}, status=503)

    try:
        data = await request.json()
        branch = data.get("branch")

        if not branch:
            return web.json_response({"error": "Branch name is required"}, status=400)

        await git.checkout(branch)
        return web.json_response({"status": "ok"})
    except Exception as e:
        logger.exception("Git checkout error: %s", e)
        return web.json_response({"error": str(e)}, status=500)
