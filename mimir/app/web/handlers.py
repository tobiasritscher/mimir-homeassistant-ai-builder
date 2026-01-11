"""HTTP request handlers for Mímir web interface."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from aiohttp import web

from ..utils.logging import get_logger
from .templates import AUDIT_HTML, CHAT_HTML, GIT_HTML, STATUS_HTML

if TYPE_CHECKING:
    from ..db.repository import AuditRepository
    from ..git.manager import GitManager

logger = get_logger(__name__)

# Type alias for aiohttp handler
Handler = Callable[[web.Request], Awaitable[web.StreamResponse]]


@web.middleware
async def request_logger_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
    """Log all incoming requests for debugging."""
    logger.debug(
        "Request: %s %s (headers: %s)",
        request.method,
        request.path,
        dict(request.headers),
    )
    try:
        response = await handler(request)
        logger.debug("Response: %s %s -> %s", request.method, request.path, response.status)
        return response
    except web.HTTPException as e:
        logger.debug(
            "Response: %s %s -> %s (HTTPException)", request.method, request.path, e.status
        )
        raise


def setup_routes(app: web.Application) -> None:
    """Set up all web routes.

    Args:
        app: The aiohttp application.
    """
    # Main pages
    app.router.add_get("/", handle_status)
    app.router.add_get("/chat", handle_chat_page)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/audit", handle_audit_page)
    app.router.add_get("/git", handle_git_page)

    # Chat API
    app.router.add_post("/api/chat", handle_chat_message)
    app.router.add_get("/api/chat/history", handle_chat_history)
    app.router.add_post("/api/chat/clear", handle_chat_clear)

    # Audit API
    app.router.add_get("/api/audit", handle_audit_list)
    app.router.add_get("/api/audit/{id}", handle_audit_detail)

    # Git API
    app.router.add_get("/api/git/status", handle_git_status)
    app.router.add_get("/api/git/commits", handle_git_commits)
    app.router.add_get("/api/git/diff/{sha}", handle_git_diff)
    app.router.add_post("/api/git/commit", handle_git_commit)
    app.router.add_post("/api/git/rollback", handle_git_rollback)
    app.router.add_get("/api/git/branches", handle_git_branches)
    app.router.add_post("/api/git/branches", handle_git_create_branch)
    app.router.add_post("/api/git/checkout", handle_git_checkout)


# ============== Main Pages ==============


async def handle_status(request: web.Request) -> web.Response:
    """Handle GET / - Main status page with chat."""
    agent = request.app.get("agent")

    if not agent:
        return web.Response(text="Agent not initialized", status=503)

    html = STATUS_HTML.format(
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


async def handle_audit_page(_request: web.Request) -> web.Response:
    """Handle GET /audit - Audit log page."""
    # Call .format() to convert doubled braces {{}} to single braces {}
    return web.Response(text=AUDIT_HTML.format(), content_type="text/html")


async def handle_git_page(_request: web.Request) -> web.Response:
    """Handle GET /git - Git history page."""
    # Call .format() to convert doubled braces {{}} to single braces {}
    return web.Response(text=GIT_HTML.format(), content_type="text/html")


async def handle_chat_page(_request: web.Request) -> web.Response:
    """Handle GET /chat - Simplified chat-only page."""
    # Call .format() to convert doubled braces {{}} to single braces {}
    return web.Response(text=CHAT_HTML.format(), content_type="text/html")


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

        # Process the message
        response = await agent._conversation_manager.process_message(
            message,
            source="web",
            user_id="web_user",
        )

        return web.json_response({"response": response})

    except Exception as e:
        logger.exception("Chat error: %s", e)
        return web.json_response(
            {"error": str(e)},
            status=500,
        )


async def handle_chat_history(request: web.Request) -> web.Response:
    """Handle GET /api/chat/history - Get conversation history."""
    agent = request.app.get("agent")

    if not agent or not agent._conversation_manager:
        return web.json_response({"history": []})

    history = agent._conversation_manager.get_history()
    return web.json_response({"history": history})


async def handle_chat_clear(request: web.Request) -> web.Response:
    """Handle POST /api/chat/clear - Clear conversation history."""
    agent = request.app.get("agent")

    if agent and agent._conversation_manager:
        agent._conversation_manager.clear_history()

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
