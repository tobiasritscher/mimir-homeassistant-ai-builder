"""HTML templates for Mímir web interface."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

# Try to import from importlib.metadata, fall back for older Python
_pkg_version: Callable[[str], str] | None = None
_PackageNotFoundError: type[Exception] = Exception

try:
    from importlib.metadata import PackageNotFoundError as _PNF
    from importlib.metadata import version as _pv

    _PackageNotFoundError = _PNF
    _pkg_version = _pv
except Exception:  # pragma: no cover
    pass


def _get_app_version() -> str:
    """Return the Mímir version shown in the web UI."""
    env_version = os.getenv("MIMIR_VERSION") or os.getenv("ADDON_VERSION")
    if env_version:
        return env_version

    if _pkg_version is None:
        return "unknown"

    try:
        return _pkg_version("mimir")
    except _PackageNotFoundError:
        return "unknown"


APP_VERSION = _get_app_version()

# Shared CSS styles (braces doubled for .format() compatibility)
SHARED_STYLES = """
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #e2e8f0;
        min-height: 100vh;
        line-height: 1.6;
    }}
    .container {{
        max-width: 1000px;
        margin: 0 auto;
        padding: 30px 20px;
    }}
    .header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 30px;
        padding-bottom: 20px;
        border-bottom: 2px solid rgba(99, 102, 241, 0.3);
    }}
    .header h1 {{
        color: #818cf8;
        font-size: 28px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    .header-icon {{
        font-size: 32px;
    }}
    .back-link {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 20px;
        background: rgba(99, 102, 241, 0.2);
        border-radius: 8px;
        color: #a5b4fc;
        text-decoration: none;
        font-size: 14px;
        transition: all 0.2s;
    }}
    .back-link:hover {{
        background: rgba(99, 102, 241, 0.3);
        color: #c7d2fe;
    }}
    .card {{
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }}
    .card h2 {{
        color: #a5b4fc;
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .btn {{
        padding: 10px 20px;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }}
    .btn-primary {{
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
    }}
    .btn-primary:hover {{
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        transform: translateY(-1px);
    }}
    .btn-secondary {{
        background: rgba(99, 102, 241, 0.2);
        color: #a5b4fc;
    }}
    .btn-secondary:hover {{
        background: rgba(99, 102, 241, 0.3);
    }}
    .btn-danger {{
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
    }}
    .btn-danger:hover {{
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
    }}
    .btn-sm {{
        padding: 6px 12px;
        font-size: 12px;
    }}
    .btn:disabled {{
        opacity: 0.5;
        cursor: not-allowed;
        transform: none;
    }}
    .input {{
        padding: 12px 16px;
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 8px;
        background: rgba(15, 23, 42, 0.6);
        color: #e2e8f0;
        font-size: 14px;
        transition: all 0.2s;
    }}
    .input:focus {{
        outline: none;
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
    }}
    .input::placeholder {{
        color: #64748b;
    }}
    .select {{
        padding: 12px 16px;
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 8px;
        background: rgba(15, 23, 42, 0.6);
        color: #e2e8f0;
        font-size: 14px;
        cursor: pointer;
        appearance: none;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236366f1'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: right 12px center;
        background-size: 16px;
        padding-right: 40px;
    }}
    .select:focus {{
        outline: none;
        border-color: #6366f1;
    }}
    .badge {{
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .badge-telegram {{ background: rgba(0, 136, 204, 0.2); color: #38bdf8; }}
    .badge-web {{ background: rgba(99, 102, 241, 0.2); color: #a5b4fc; }}
    .badge-user {{ background: rgba(34, 197, 94, 0.2); color: #4ade80; }}
    .badge-assistant {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; }}
    .badge-tool {{ background: rgba(239, 68, 68, 0.2); color: #f87171; }}
    .badge-error {{ background: rgba(239, 68, 68, 0.2); color: #f87171; }}
    .modal-overlay {{
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(4px);
        z-index: 1000;
        align-items: center;
        justify-content: center;
        padding: 20px;
    }}
    .modal-overlay.visible {{
        display: flex;
    }}
    .modal {{
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 16px;
        padding: 28px;
        max-width: 450px;
        width: 100%;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
    }}
    .modal h3 {{
        color: #e2e8f0;
        font-size: 20px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .modal p {{
        color: #94a3b8;
        margin-bottom: 12px;
    }}
    .modal-buttons {{
        display: flex;
        gap: 12px;
        justify-content: flex-end;
        margin-top: 24px;
    }}
    .empty-state {{
        text-align: center;
        padding: 60px 20px;
        color: #64748b;
    }}
    .empty-state-icon {{
        font-size: 48px;
        margin-bottom: 16px;
        opacity: 0.5;
    }}
    .loading {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        color: #64748b;
        padding: 40px;
    }}
    .spinner {{
        width: 20px;
        height: 20px;
        border: 2px solid rgba(99, 102, 241, 0.3);
        border-top-color: #6366f1;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }}
    @keyframes spin {{
        to {{ transform: rotate(360deg); }}
    }}
"""

# Main status page with chat interface
STATUS_HTML = (
    """<!DOCTYPE html>
<html>
<head>
    <title>Mimir - Home Assistant Agent</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        """
    + SHARED_STYLES
    + """
        .status-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }}
        .status-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid rgba(99, 102, 241, 0.1);
        }}
        .status-item:last-child {{
            border-bottom: none;
        }}
        .status-label {{
            color: #94a3b8;
            font-size: 14px;
        }}
        .status-value {{
            font-weight: 500;
            color: #e2e8f0;
        }}
        .status-ok {{ color: #4ade80; }}
        .status-error {{ color: #f87171; }}

        .chat-container {{
            display: flex;
            flex-direction: column;
            height: 450px;
        }}
        .chat-messages {{
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            background: rgba(15, 23, 42, 0.5);
            border-radius: 12px;
            margin-bottom: 16px;
        }}
        .message {{
            margin: 12px 0;
            padding: 12px 16px;
            border-radius: 12px;
            max-width: 85%;
            word-wrap: break-word;
            animation: fadeIn 0.3s ease;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .message.user {{
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }}
        .message.assistant {{
            background: rgba(51, 65, 85, 0.8);
            border-bottom-left-radius: 4px;
        }}
        .message pre {{
            background: rgba(0, 0, 0, 0.3);
            padding: 12px;
            border-radius: 8px;
            overflow-x: auto;
            white-space: pre-wrap;
            margin: 8px 0;
            font-size: 13px;
        }}
        .message code {{
            background: rgba(0, 0, 0, 0.3);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 13px;
        }}
        .chat-input-container {{
            display: flex;
            gap: 12px;
        }}
        .chat-input {{
            flex: 1;
            padding: 14px 18px;
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 12px;
            background: rgba(15, 23, 42, 0.6);
            color: #e2e8f0;
            font-size: 14px;
        }}
        .chat-input:focus {{
            outline: none;
            border-color: #6366f1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }}
        .chat-send {{
            padding: 14px 28px;
            border: none;
            border-radius: 12px;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .chat-send:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        }}
        .chat-send:disabled {{
            opacity: 0.5;
            transform: none;
            box-shadow: none;
        }}
        .chat-note {{
            font-size: 12px;
            color: #64748b;
            margin-top: 12px;
            text-align: center;
        }}
        .typing-indicator {{
            display: none;
            padding: 12px 16px;
            background: rgba(51, 65, 85, 0.8);
            border-radius: 12px;
            max-width: 80px;
            margin: 8px 0;
        }}
        .typing-indicator.visible {{
            display: block;
        }}
        .typing-dot {{
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #6366f1;
            border-radius: 50%;
            margin: 0 2px;
            animation: typing 1s infinite;
        }}
        .typing-dot:nth-child(2) {{ animation-delay: 0.2s; }}
        .typing-dot:nth-child(3) {{ animation-delay: 0.4s; }}
        @keyframes typing {{
            0%, 100% {{ opacity: 0.3; }}
            50% {{ opacity: 1; }}
        }}
        .nav-links {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }}
        .nav-link {{
            padding: 14px 24px;
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 12px;
            color: #a5b4fc;
            text-decoration: none;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .nav-link:hover {{
            background: rgba(99, 102, 241, 0.2);
            border-color: rgba(99, 102, 241, 0.4);
            transform: translateY(-2px);
        }}
        .nav-icon {{
            font-size: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><span class="header-icon">&#129704;</span> Mimir</h1>
        </div>

        <div class="card">
            <h2>&#128202; Status</h2>
            <div class="status-item">
                <span class="status-label">Version</span>
                <span class="status-value">{version}</span>
            </div>
            <div class="status-item">
                <span class="status-label">LLM Provider</span>
                <span class="status-value">{llm_provider}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Model</span>
                <span class="status-value">{llm_model}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Operating Mode</span>
                <span class="status-value">{operating_mode}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Home Assistant</span>
                <span class="status-value {ha_status_class}">{ha_status}</span>
            </div>
            <div class="status-item">
                <span class="status-label">WebSocket</span>
                <span class="status-value {ws_status_class}">{ws_status}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Registered Tools</span>
                <span class="status-value">{tool_count}</span>
            </div>
        </div>

        <div class="card">
            <h2>&#128172; Chat with Mimir</h2>
            <div class="chat-container">
                <div class="chat-messages" id="chatMessages"></div>
                <div class="typing-indicator" id="typingIndicator">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
                <div class="chat-input-container">
                    <input type="text" class="chat-input" id="chatInput"
                           placeholder="Ask Mimir something..."
                           onkeypress="if(event.key==='Enter')sendMessage()">
                    <button class="chat-send" id="sendBtn" onclick="sendMessage()">Send</button>
                </div>
            </div>
            <p class="chat-note">&#128279; This chat shares history with your Telegram conversation</p>
        </div>

        <div class="nav-links">
            <a href="." class="nav-link">
                <span class="nav-icon">&#128172;</span>
                Back to Chat
            </a>
            <a href="audit" class="nav-link">
                <span class="nav-icon">&#128220;</span>
                Audit Logs
            </a>
            <a href="git" class="nav-link">
                <span class="nav-icon">&#128230;</span>
                Git History
            </a>
        </div>
    </div>

    <script>
        function formatMessage(text) {{
            text = text.replace(/```([\\s\\S]*?)```/g, '<pre>$1</pre>');
            text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
            text = text.replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>');
            text = text.replace(/\\n/g, '<br>');
            return text;
        }}

        function addMessage(role, content) {{
            const messages = document.getElementById('chatMessages');
            const div = document.createElement('div');
            div.className = 'message ' + role;
            div.innerHTML = formatMessage(content);
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }}

        function setTyping(visible) {{
            document.getElementById('typingIndicator').className = 'typing-indicator' + (visible ? ' visible' : '');
        }}

        async function sendMessage() {{
            const input = document.getElementById('chatInput');
            const btn = document.getElementById('sendBtn');
            const message = input.value.trim();
            if (!message) return;

            addMessage('user', message);
            input.value = '';
            btn.disabled = true;
            setTyping(true);

            try {{
                const response = await fetch('api/chat', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ message: message }})
                }});
                if (!response.ok) {{
                    const text = await response.text();
                    addMessage('assistant', 'Error (' + response.status + '): ' + text.substring(0, 200));
                    return;
                }}
                const data = await response.json();
                addMessage('assistant', data.error ? 'Error: ' + data.error : data.response);
            }} catch (error) {{
                addMessage('assistant', 'Error: ' + error.message);
            }}

            btn.disabled = false;
            setTyping(false);
            input.focus();
        }}

        async function loadHistory() {{
            try {{
                const response = await fetch('api/chat/history');
                const data = await response.json();
                if (data.history) {{
                    data.history.forEach(msg => addMessage(msg.role, msg.content));
                }}
            }} catch (error) {{
                console.error('Failed to load history:', error);
            }}
        }}

        loadHistory();
    </script>
</body>
</html>
"""
)

# Inline the version so the dashboard doesn't depend on a `{version}` placeholder from the backend.
STATUS_HTML = STATUS_HTML.replace("{version}", APP_VERSION)

# Audit log page
AUDIT_HTML = (
    """<!DOCTYPE html>
<html>
<head>
    <title>Audit Logs - Mimir</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        """
    + SHARED_STYLES
    + """
        .filters {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 24px;
        }}
        .log-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
        }}
        .log-table th {{
            text-align: left;
            padding: 14px 16px;
            color: #94a3b8;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid rgba(99, 102, 241, 0.2);
        }}
        .log-table td {{
            padding: 14px 16px;
            border-bottom: 1px solid rgba(99, 102, 241, 0.1);
            vertical-align: middle;
        }}
        .log-table tr {{
            cursor: pointer;
            transition: all 0.2s;
        }}
        .log-table tbody tr:hover {{
            background: rgba(99, 102, 241, 0.1);
        }}
        .content-preview {{
            max-width: 350px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            color: #94a3b8;
            font-size: 13px;
        }}
        .timestamp {{
            font-size: 13px;
            color: #64748b;
            white-space: nowrap;
        }}
        .pagination {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 16px;
            margin-top: 24px;
            padding-top: 20px;
            border-top: 1px solid rgba(99, 102, 241, 0.1);
        }}
        .page-info {{
            color: #94a3b8;
            font-size: 14px;
        }}
        .detail-section {{
            margin-bottom: 20px;
        }}
        .detail-section h4 {{
            color: #a5b4fc;
            font-size: 14px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .detail-content {{
            background: rgba(15, 23, 42, 0.6);
            border-radius: 8px;
            padding: 16px;
            font-size: 13px;
            white-space: pre-wrap;
            word-break: break-word;
            max-height: 300px;
            overflow-y: auto;
        }}
        .tool-card {{
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 12px;
        }}
        .tool-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .tool-name {{
            font-weight: 600;
            color: #e2e8f0;
        }}
        .tool-meta {{
            display: flex;
            gap: 16px;
            font-size: 12px;
            color: #64748b;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><span class="header-icon">&#128220;</span> Audit Logs</h1>
            <a href="." class="back-link">&#8592; Dashboard</a>
        </div>

        <div class="card">
            <div class="filters">
                <select class="select" id="filterSource">
                    <option value="">All Sources</option>
                    <option value="telegram">Telegram</option>
                    <option value="web">Web</option>
                </select>
                <select class="select" id="filterType">
                    <option value="">All Types</option>
                    <option value="user">User</option>
                    <option value="assistant">Assistant</option>
                    <option value="tool">Tool</option>
                    <option value="error">Error</option>
                </select>
                <input type="text" class="input" id="filterSearch" placeholder="Search content..." style="flex: 1; min-width: 200px;">
                <button class="btn btn-primary" onclick="applyFilters()">&#128269; Search</button>
            </div>

            <table class="log-table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Source</th>
                        <th>Type</th>
                        <th>Content</th>
                    </tr>
                </thead>
                <tbody id="logsTable">
                    <tr><td colspan="4" class="loading"><div class="spinner"></div> Loading...</td></tr>
                </tbody>
            </table>

            <div class="pagination">
                <button class="btn btn-secondary" id="prevBtn" onclick="prevPage()" disabled>&#8592; Previous</button>
                <span class="page-info" id="pageInfo">Page 1</span>
                <button class="btn btn-secondary" id="nextBtn" onclick="nextPage()">Next &#8594;</button>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="detailModal">
        <div class="modal" style="max-width: 700px;">
            <h3>&#128196; Log Details</h3>
            <div id="detailBody"></div>
            <div class="modal-buttons">
                <button class="btn btn-secondary" onclick="closeModal()">Close</button>
            </div>
        </div>
    </div>

    <script>
        let currentPage = 0;
        const pageSize = 20;

        function formatTime(timestamp) {{
            return new Date(timestamp).toLocaleString();
        }}

        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}

        function getBadgeClass(type) {{
            const classes = {{ telegram: 'badge-telegram', web: 'badge-web', user: 'badge-user', assistant: 'badge-assistant', tool: 'badge-tool', error: 'badge-error' }};
            return classes[type] || '';
        }}

        async function loadLogs() {{
            const source = document.getElementById('filterSource').value;
            const type = document.getElementById('filterType').value;
            const search = document.getElementById('filterSearch').value;

            let url = `api/audit?limit=${{pageSize}}&offset=${{currentPage * pageSize}}`;
            if (source) url += `&source=${{source}}`;
            if (type) url += `&type=${{type}}`;
            if (search) url += `&search=${{encodeURIComponent(search)}}`;

            const tbody = document.getElementById('logsTable');
            tbody.innerHTML = '<tr><td colspan="4" class="loading"><div class="spinner"></div> Loading...</td></tr>';

            try {{
                const response = await fetch(url);
                const data = await response.json();

                if (!data.logs || data.logs.length === 0) {{
                    tbody.innerHTML = '<tr><td colspan="4" class="empty-state"><div class="empty-state-icon">&#128220;</div>No logs found</td></tr>';
                    return;
                }}

                tbody.innerHTML = data.logs.map(log => `
                    <tr onclick="showDetail(${{log.id}})">
                        <td class="timestamp">${{formatTime(log.timestamp)}}</td>
                        <td><span class="badge ${{getBadgeClass(log.source)}}">${{log.source}}</span></td>
                        <td><span class="badge ${{getBadgeClass(log.message_type)}}">${{log.message_type}}</span></td>
                        <td class="content-preview">${{escapeHtml(log.content.substring(0, 100))}}</td>
                    </tr>
                `).join('');

                document.getElementById('pageInfo').textContent = `Page ${{currentPage + 1}}`;
                document.getElementById('prevBtn').disabled = currentPage === 0;
                document.getElementById('nextBtn').disabled = data.logs.length < pageSize;
            }} catch (error) {{
                tbody.innerHTML = '<tr><td colspan="4" class="empty-state">Failed to load logs</td></tr>';
            }}
        }}

        async function showDetail(id) {{
            try {{
                const response = await fetch(`api/audit/${{id}}`);
                const log = await response.json();

                let html = `
                    <div class="detail-section">
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 16px;">
                            <div><strong style="color: #94a3b8;">Timestamp:</strong> ${{formatTime(log.timestamp)}}</div>
                            <div><strong style="color: #94a3b8;">Source:</strong> <span class="badge ${{getBadgeClass(log.source)}}">${{log.source}}</span></div>
                            <div><strong style="color: #94a3b8;">Type:</strong> <span class="badge ${{getBadgeClass(log.message_type)}}">${{log.message_type}}</span></div>
                            <div><strong style="color: #94a3b8;">User:</strong> ${{log.user_id || 'N/A'}}</div>
                        </div>
                    </div>
                    <div class="detail-section">
                        <h4>&#128172; Content</h4>
                        <div class="detail-content">${{escapeHtml(log.content)}}</div>
                    </div>
                `;

                if (log.tool_executions && log.tool_executions.length > 0) {{
                    html += '<div class="detail-section"><h4>&#128295; Tool Executions</h4>';
                    log.tool_executions.forEach(tool => {{
                        html += `
                            <div class="tool-card">
                                <div class="tool-header">
                                    <span class="tool-name">${{tool.tool_name}}</span>
                                    <span class="badge ${{tool.success ? 'badge-user' : 'badge-error'}}">${{tool.success ? 'Success' : 'Failed'}}</span>
                                </div>
                                <div class="tool-meta">
                                    <span>&#9201; ${{tool.duration_ms}}ms</span>
                                </div>
                                <details style="margin-top: 12px;">
                                    <summary style="cursor: pointer; color: #a5b4fc; font-size: 13px;">Parameters</summary>
                                    <div class="detail-content" style="margin-top: 8px; font-family: monospace;">${{escapeHtml(JSON.stringify(tool.parameters, null, 2))}}</div>
                                </details>
                                ${{tool.result ? `
                                <details style="margin-top: 8px;">
                                    <summary style="cursor: pointer; color: #a5b4fc; font-size: 13px;">Result</summary>
                                    <div class="detail-content" style="margin-top: 8px;">${{escapeHtml(tool.result)}}</div>
                                </details>` : ''}}
                            </div>
                        `;
                    }});
                    html += '</div>';
                }}

                document.getElementById('detailBody').innerHTML = html;
                document.getElementById('detailModal').classList.add('visible');
            }} catch (error) {{
                console.error('Failed to load detail:', error);
            }}
        }}

        function closeModal() {{
            document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('visible'));
        }}

        function applyFilters() {{ currentPage = 0; loadLogs(); }}
        function prevPage() {{ if (currentPage > 0) {{ currentPage--; loadLogs(); }} }}
        function nextPage() {{ currentPage++; loadLogs(); }}

        loadLogs();
    </script>
</body>
</html>
"""
)

# Git history page
GIT_HTML = (
    """<!DOCTYPE html>
<html>
<head>
    <title>Git History - Mimir</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        """
    + SHARED_STYLES
    + """
        .status-bar {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 16px 20px;
            background: rgba(15, 23, 42, 0.6);
            border-radius: 10px;
            margin-bottom: 24px;
            border-left: 4px solid #64748b;
        }}
        .status-bar.clean {{
            border-left-color: #4ade80;
            background: rgba(34, 197, 94, 0.1);
        }}
        .status-bar.dirty {{
            border-left-color: #fbbf24;
            background: rgba(245, 158, 11, 0.1);
        }}
        .status-icon {{
            font-size: 20px;
        }}
        .status-text {{
            flex: 1;
        }}
        .branch-bar {{
            display: flex;
            gap: 12px;
            margin-bottom: 24px;
            align-items: center;
        }}
        .branch-label {{
            color: #94a3b8;
            font-size: 14px;
        }}
        .commit {{
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(99, 102, 241, 0.15);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            transition: all 0.2s;
        }}
        .commit:hover {{
            border-color: rgba(99, 102, 241, 0.3);
            background: rgba(15, 23, 42, 0.8);
        }}
        .commit-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 16px;
        }}
        .commit-info {{
            flex: 1;
        }}
        .commit-message {{
            font-weight: 600;
            color: #e2e8f0;
            font-size: 15px;
            margin-bottom: 8px;
            line-height: 1.4;
        }}
        .commit-meta {{
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            font-size: 13px;
            color: #64748b;
        }}
        .commit-meta span {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .commit-sha {{
            font-family: 'SF Mono', 'Fira Code', monospace;
            color: #818cf8;
            background: rgba(99, 102, 241, 0.15);
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .commit-actions {{
            display: flex;
            gap: 8px;
            flex-shrink: 0;
        }}
        .diff-view {{
            background: rgba(0, 0, 0, 0.4);
            border-radius: 8px;
            padding: 16px;
            margin-top: 16px;
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 12px;
            line-height: 1.6;
            overflow-x: auto;
            white-space: pre;
            display: none;
            max-height: 400px;
            overflow-y: auto;
        }}
        .diff-view.visible {{
            display: block;
            animation: fadeIn 0.3s ease;
        }}
        .diff-add {{ color: #4ade80; }}
        .diff-remove {{ color: #f87171; }}
        .diff-header {{ color: #818cf8; font-weight: 600; }}
        .diff-file {{ color: #fbbf24; }}
        .warning-text {{
            color: #fbbf24;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><span class="header-icon">&#128230;</span> Configuration History</h1>
            <a href="." class="back-link">&#8592; Dashboard</a>
        </div>

        <div class="card">
            <div id="statusBar" class="status-bar">
                <span class="status-icon">&#8987;</span>
                <span class="status-text">Loading status...</span>
            </div>

            <div class="branch-bar">
                <span class="branch-label">&#128279; Branch:</span>
                <select class="select" id="branchSelect" onchange="switchBranch()">
                    <option>Loading...</option>
                </select>
                <button class="btn btn-secondary" onclick="showNewBranchModal()">+ New Branch</button>
            </div>

            <h2>&#128197; Recent Commits</h2>
            <div id="commits">
                <div class="loading"><div class="spinner"></div> Loading commits...</div>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="newBranchModal">
        <div class="modal">
            <h3>&#128279; Create New Branch</h3>
            <p>Create a new branch from the current HEAD.</p>
            <input type="text" class="input" id="newBranchName" placeholder="Branch name (e.g., backup-jan-10)" style="width: 100%; margin-top: 12px;">
            <div class="modal-buttons">
                <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn btn-primary" onclick="createBranch()">Create Branch</button>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="rollbackModal">
        <div class="modal">
            <h3>&#9888;&#65039; Confirm Rollback</h3>
            <p>Are you sure you want to rollback to commit <code id="rollbackSha" class="commit-sha"></code>?</p>
            <p class="warning-text">&#9888;&#65039; This will create a new commit reverting all changes since that point.</p>
            <div class="modal-buttons">
                <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn btn-danger" onclick="confirmRollback()">Rollback</button>
            </div>
        </div>
    </div>

    <script>
        let currentRollbackSha = null;

        function formatDate(dateStr) {{
            const date = new Date(dateStr);
            return date.toLocaleDateString() + ' at ' + date.toLocaleTimeString([], {{hour: '2-digit', minute:'2-digit'}});
        }}

        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}

        function formatDiff(diff) {{
            return diff.split('\\n').map(line => {{
                if (line.startsWith('+') && !line.startsWith('+++')) {{
                    return `<span class="diff-add">${{escapeHtml(line)}}</span>`;
                }} else if (line.startsWith('-') && !line.startsWith('---')) {{
                    return `<span class="diff-remove">${{escapeHtml(line)}}</span>`;
                }} else if (line.startsWith('@@')) {{
                    return `<span class="diff-header">${{escapeHtml(line)}}</span>`;
                }} else if (line.startsWith('diff') || line.startsWith('index') || line.startsWith('---') || line.startsWith('+++')) {{
                    return `<span class="diff-file">${{escapeHtml(line)}}</span>`;
                }}
                return escapeHtml(line);
            }}).join('\\n');
        }}

        async function loadStatus() {{
            try {{
                const response = await fetch('api/git/status');
                const data = await response.json();
                const statusBar = document.getElementById('statusBar');
                if (data.clean) {{
                    statusBar.className = 'status-bar clean';
                    statusBar.innerHTML = '<span class="status-icon">&#10003;</span><span class="status-text">Working directory clean - all changes committed</span>';
                }} else {{
                    statusBar.className = 'status-bar dirty';
                    statusBar.innerHTML = `<span class="status-icon">&#9888;</span><span class="status-text">${{data.changed_files || 0}} file(s) with uncommitted changes</span><button class="btn btn-primary" onclick="commitChanges()" style="margin-left: auto;">&#128190; Commit All</button>`;
                }}
            }} catch (error) {{
                document.getElementById('statusBar').innerHTML = '<span class="status-icon">&#10060;</span><span class="status-text">Failed to load status</span>';
            }}
        }}

        async function commitChanges() {{
            const statusBar = document.getElementById('statusBar');
            statusBar.innerHTML = '<span class="status-icon"><div class="spinner"></div></span><span class="status-text">Committing changes...</span>';

            try {{
                const response = await fetch('api/git/commit', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }}
                }});
                const data = await response.json();

                if (data.status === 'ok') {{
                    statusBar.className = 'status-bar clean';
                    statusBar.innerHTML = `<span class="status-icon">&#10003;</span><span class="status-text">Committed: ${{escapeHtml(data.message)}}</span>`;
                    loadCommits();  // Refresh commits list
                }} else if (data.status === 'no_changes') {{
                    statusBar.className = 'status-bar clean';
                    statusBar.innerHTML = '<span class="status-icon">&#10003;</span><span class="status-text">No changes to commit</span>';
                }} else {{
                    statusBar.className = 'status-bar dirty';
                    statusBar.innerHTML = `<span class="status-icon">&#10060;</span><span class="status-text">Commit failed: ${{escapeHtml(data.error || 'Unknown error')}}</span>`;
                }}

                // Reload status after a brief delay
                setTimeout(loadStatus, 2000);
            }} catch (error) {{
                statusBar.className = 'status-bar dirty';
                statusBar.innerHTML = '<span class="status-icon">&#10060;</span><span class="status-text">Failed to commit: ' + error.message + '</span>';
                setTimeout(loadStatus, 2000);
            }}
        }}

        async function loadBranches() {{
            try {{
                const response = await fetch('api/git/branches');
                const data = await response.json();
                const select = document.getElementById('branchSelect');
                if (!data.branches || data.branches.length === 0) {{
                    select.innerHTML = '<option>No branches</option>';
                    return;
                }}
                select.innerHTML = data.branches.map(b =>
                    `<option value="${{b.name}}" ${{b.current ? 'selected' : ''}}>${{b.name}}${{b.current ? ' (current)' : ''}}</option>`
                ).join('');
            }} catch (error) {{
                document.getElementById('branchSelect').innerHTML = '<option>Error loading</option>';
            }}
        }}

        async function loadCommits() {{
            const container = document.getElementById('commits');
            container.innerHTML = '<div class="loading"><div class="spinner"></div> Loading commits...</div>';

            try {{
                const response = await fetch('api/git/commits?limit=20');
                const data = await response.json();

                if (!data.commits || data.commits.length === 0) {{
                    container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">&#128230;</div>No commits yet</div>';
                    return;
                }}

                container.innerHTML = data.commits.map(commit => `
                    <div class="commit">
                        <div class="commit-header">
                            <div class="commit-info">
                                <div class="commit-message">${{escapeHtml(commit.message)}}</div>
                                <div class="commit-meta">
                                    <span>&#128100; ${{escapeHtml(commit.author)}}</span>
                                    <span>&#128197; ${{formatDate(commit.date)}}</span>
                                    <span class="commit-sha">${{commit.sha.substring(0, 8)}}</span>
                                </div>
                            </div>
                            <div class="commit-actions">
                                <button class="btn btn-secondary btn-sm" onclick="toggleDiff('${{commit.sha}}')">&#128065; Diff</button>
                                <button class="btn btn-danger btn-sm" onclick="showRollbackModal('${{commit.sha}}')">&#8634; Rollback</button>
                            </div>
                        </div>
                        <div class="diff-view" id="diff-${{commit.sha}}"></div>
                    </div>
                `).join('');
            }} catch (error) {{
                container.innerHTML = '<div class="empty-state">Failed to load commits</div>';
            }}
        }}

        async function toggleDiff(sha) {{
            const diffView = document.getElementById(`diff-${{sha}}`);
            if (diffView.classList.contains('visible')) {{
                diffView.classList.remove('visible');
                return;
            }}
            diffView.innerHTML = '<div class="loading"><div class="spinner"></div> Loading diff...</div>';
            diffView.classList.add('visible');

            try {{
                const response = await fetch(`api/git/diff/${{sha}}`);
                const data = await response.json();
                diffView.innerHTML = formatDiff(data.diff || 'No changes in this commit');
            }} catch (error) {{
                diffView.innerHTML = 'Failed to load diff';
            }}
        }}

        async function switchBranch() {{
            const branch = document.getElementById('branchSelect').value;
            try {{
                await fetch('api/git/checkout', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ branch: branch }})
                }});
                loadCommits();
                loadStatus();
                loadBranches();
            }} catch (error) {{
                alert('Failed to switch branch');
            }}
        }}

        function showNewBranchModal() {{
            document.getElementById('newBranchModal').classList.add('visible');
            document.getElementById('newBranchName').value = '';
            document.getElementById('newBranchName').focus();
        }}

        function showRollbackModal(sha) {{
            currentRollbackSha = sha;
            document.getElementById('rollbackSha').textContent = sha.substring(0, 8);
            document.getElementById('rollbackModal').classList.add('visible');
        }}

        function closeModal() {{
            document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('visible'));
        }}

        async function createBranch() {{
            const name = document.getElementById('newBranchName').value.trim();
            if (!name) return;
            try {{
                await fetch('api/git/branches', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ name: name }})
                }});
                closeModal();
                loadBranches();
            }} catch (error) {{
                alert('Failed to create branch');
            }}
        }}

        async function confirmRollback() {{
            if (!currentRollbackSha) return;
            try {{
                const response = await fetch('api/git/rollback', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ sha: currentRollbackSha }})
                }});
                if (response.ok) {{
                    closeModal();
                    loadCommits();
                    loadStatus();
                    alert('Rollback successful!');
                }} else {{
                    const data = await response.json();
                    alert('Rollback failed: ' + (data.error || 'Unknown error'));
                }}
            }} catch (error) {{
                alert('Failed to rollback: ' + error.message);
            }}
        }}

        // Initialize
        loadStatus();
        loadBranches();
        loadCommits();

        // Close modal on escape
        document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeModal(); }});
    </script>
</body>
</html>
"""
)

# Simplified chat-only page
CHAT_HTML = (
    """<!DOCTYPE html>
<html>
<head>
    <title>Chat - Mimir</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        """
    + SHARED_STYLES
    + """
        .chat-page {{
            display: flex;
            flex-direction: column;
            height: 100vh;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        .chat-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(99, 102, 241, 0.2);
            margin-bottom: 16px;
            flex-shrink: 0;
        }}
        .chat-header h1 {{
            color: #818cf8;
            font-size: 24px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .header-actions {{
            display: flex;
            gap: 8px;
        }}
        .quick-actions {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 16px;
            flex-shrink: 0;
        }}
        .quick-btn {{
            padding: 8px 14px;
            background: rgba(99, 102, 241, 0.15);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 20px;
            color: #a5b4fc;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .quick-btn:hover {{
            background: rgba(99, 102, 241, 0.25);
            border-color: rgba(99, 102, 241, 0.5);
            transform: translateY(-1px);
        }}
        .chat-main {{
            flex: 1;
            display: flex;
            flex-direction: column;
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 16px;
            overflow: hidden;
            min-height: 0;
        }}
        .chat-messages {{
            flex: 1;
            overflow-y: auto;
            padding: 20px;
        }}
        .message {{
            margin: 12px 0;
            padding: 14px 18px;
            border-radius: 16px;
            max-width: 85%;
            word-wrap: break-word;
            animation: fadeIn 0.3s ease;
            line-height: 1.5;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .message.user {{
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }}
        .message.assistant {{
            background: rgba(51, 65, 85, 0.9);
            border-bottom-left-radius: 4px;
        }}
        .message pre {{
            background: rgba(0, 0, 0, 0.3);
            padding: 12px;
            border-radius: 8px;
            overflow-x: auto;
            white-space: pre-wrap;
            margin: 10px 0;
            font-size: 13px;
        }}
        .message code {{
            background: rgba(0, 0, 0, 0.3);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 13px;
        }}
        .typing-indicator {{
            display: none;
            padding: 14px 18px;
            background: rgba(51, 65, 85, 0.9);
            border-radius: 16px;
            border-bottom-left-radius: 4px;
            max-width: 80px;
            margin: 12px 0;
        }}
        .typing-indicator.visible {{
            display: block;
        }}
        .typing-dot {{
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #6366f1;
            border-radius: 50%;
            margin: 0 2px;
            animation: typing 1s infinite;
        }}
        .typing-dot:nth-child(2) {{ animation-delay: 0.2s; }}
        .typing-dot:nth-child(3) {{ animation-delay: 0.4s; }}
        @keyframes typing {{
            0%, 100% {{ opacity: 0.3; }}
            50% {{ opacity: 1; }}
        }}
        .chat-input-area {{
            padding: 16px 20px;
            background: rgba(15, 23, 42, 0.6);
            border-top: 1px solid rgba(99, 102, 241, 0.1);
        }}
        .chat-input-container {{
            display: flex;
            gap: 12px;
        }}
        .chat-input {{
            flex: 1;
            padding: 14px 18px;
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 12px;
            background: rgba(30, 41, 59, 0.8);
            color: #e2e8f0;
            font-size: 15px;
            resize: none;
            max-height: 120px;
        }}
        .chat-input:focus {{
            outline: none;
            border-color: #6366f1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }}
        .chat-send {{
            padding: 14px 24px;
            border: none;
            border-radius: 12px;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            font-weight: 500;
            font-size: 15px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .chat-send:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        }}
        .chat-send:disabled {{
            opacity: 0.5;
            transform: none;
            box-shadow: none;
            cursor: not-allowed;
        }}
        .welcome-message {{
            text-align: center;
            padding: 60px 20px;
            color: #64748b;
        }}
        .welcome-message h2 {{
            color: #818cf8;
            font-size: 22px;
            margin-bottom: 12px;
        }}
        .welcome-message p {{
            margin-bottom: 20px;
        }}
        .suggestions {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 8px;
            margin-top: 20px;
        }}
        .suggestion {{
            padding: 10px 16px;
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 20px;
            color: #a5b4fc;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .suggestion:hover {{
            background: rgba(99, 102, 241, 0.2);
            border-color: rgba(99, 102, 241, 0.4);
        }}
    </style>
</head>
<body>
    <div class="chat-page">
        <div class="chat-header">
            <h1>&#129704; Mimir</h1>
            <div class="header-actions">
                <a href="status" class="btn btn-secondary">&#128202; Status</a>
                <a href="audit" class="btn btn-secondary">&#128220; Audit</a>
                <a href="git" class="btn btn-secondary">&#128230; Git</a>
            </div>
        </div>

        <div class="quick-actions">
            <button class="quick-btn" onclick="sendQuickAction('Analyze recent Home Assistant error logs')">
                &#128270; Analyze Logs
            </button>
            <button class="quick-btn" onclick="sendQuickAction('What entities have changed state in the last hour?')">
                &#128200; Recent Changes
            </button>
            <button class="quick-btn" onclick="sendQuickAction('Show me a summary of my automations')">
                &#9881; Automations
            </button>
            <button class="quick-btn" onclick="sendQuickAction('What devices are currently unavailable?')">
                &#128268; Unavailable
            </button>
        </div>

        <div class="chat-main">
            <div class="chat-messages" id="chatMessages">
                <div class="welcome-message" id="welcomeMessage">
                    <h2>Welcome to Mimir</h2>
                    <p>Your intelligent Home Assistant assistant. Ask me anything about your smart home!</p>
                    <div class="suggestions">
                        <span class="suggestion" onclick="sendQuickAction('Turn off all lights')">Turn off all lights</span>
                        <span class="suggestion" onclick="sendQuickAction('What is the temperature in the living room?')">Check temperature</span>
                        <span class="suggestion" onclick="sendQuickAction('Create an automation to turn on lights at sunset')">Create automation</span>
                    </div>
                </div>
            </div>
            <div class="typing-indicator" id="typingIndicator">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
            <div class="chat-input-area">
                <div class="chat-input-container">
                    <textarea class="chat-input" id="chatInput" rows="1"
                           placeholder="Ask Mimir something..."
                           onkeydown="handleKeyDown(event)"></textarea>
                    <button class="chat-send" id="sendBtn" onclick="sendMessage()">
                        Send &#10148;
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        function formatMessage(text) {{
            text = text.replace(/```([\\s\\S]*?)```/g, '<pre>$1</pre>');
            text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
            text = text.replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>');
            text = text.replace(/\\n/g, '<br>');
            return text;
        }}

        function addMessage(role, content) {{
            const welcome = document.getElementById('welcomeMessage');
            if (welcome) welcome.style.display = 'none';

            const messages = document.getElementById('chatMessages');
            const div = document.createElement('div');
            div.className = 'message ' + role;
            div.innerHTML = formatMessage(content);
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }}

        function setTyping(visible) {{
            document.getElementById('typingIndicator').className = 'typing-indicator' + (visible ? ' visible' : '');
        }}

        function handleKeyDown(event) {{
            if (event.key === 'Enter' && !event.shiftKey) {{
                event.preventDefault();
                sendMessage();
            }}
        }}

        async function sendMessage(customMessage) {{
            const input = document.getElementById('chatInput');
            const btn = document.getElementById('sendBtn');
            const message = customMessage || input.value.trim();
            if (!message) return;

            addMessage('user', message);
            if (!customMessage) input.value = '';
            btn.disabled = true;
            setTyping(true);

            try {{
                const response = await fetch('api/chat', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ message: message }})
                }});
                if (!response.ok) {{
                    const text = await response.text();
                    addMessage('assistant', 'Error (' + response.status + '): ' + text.substring(0, 200));
                    return;
                }}
                const data = await response.json();
                addMessage('assistant', data.error ? 'Error: ' + data.error : data.response);
            }} catch (error) {{
                addMessage('assistant', 'Error: ' + error.message);
            }}

            btn.disabled = false;
            setTyping(false);
            input.focus();
        }}

        function sendQuickAction(message) {{
            sendMessage(message);
        }}

        async function loadHistory() {{
            try {{
                const response = await fetch('api/chat/history');
                const data = await response.json();
                if (data.history && data.history.length > 0) {{
                    document.getElementById('welcomeMessage').style.display = 'none';
                    data.history.forEach(msg => addMessage(msg.role, msg.content));
                }}
            }} catch (error) {{
                console.error('Failed to load history:', error);
            }}
        }}

        // Auto-resize textarea
        const textarea = document.getElementById('chatInput');
        textarea.addEventListener('input', function() {{
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        }});

        loadHistory();
    </script>
</body>
</html>
"""
)
