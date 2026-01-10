"""HTML templates for Mímir web interface."""

# Main status page with chat interface
STATUS_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Mimir - Home Assistant Agent</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        h1 {{
            color: #6366f1;
            border-bottom: 2px solid #6366f1;
            padding-bottom: 10px;
            margin-bottom: 5px;
        }}
        .subtitle {{
            color: #888;
            margin-bottom: 20px;
        }}
        .card {{
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }}
        .card h2 {{
            margin-top: 0;
            color: #a5b4fc;
        }}
        .status-item {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .status-item:last-child {{
            border-bottom: none;
        }}
        .status-ok {{ color: #22c55e; }}
        .status-error {{ color: #ef4444; }}
        .status-pending {{ color: #f59e0b; }}

        /* Chat styles */
        .chat-container {{
            display: flex;
            flex-direction: column;
            height: 400px;
        }}
        .chat-messages {{
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            margin-bottom: 10px;
        }}
        .message {{
            margin: 10px 0;
            padding: 10px 15px;
            border-radius: 10px;
            max-width: 80%;
            word-wrap: break-word;
        }}
        .message.user {{
            background: #6366f1;
            margin-left: auto;
        }}
        .message.assistant {{
            background: rgba(255,255,255,0.15);
        }}
        .message pre {{
            background: rgba(0,0,0,0.3);
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
            white-space: pre-wrap;
        }}
        .message code {{
            background: rgba(0,0,0,0.3);
            padding: 2px 5px;
            border-radius: 3px;
        }}
        .chat-input-container {{
            display: flex;
            gap: 10px;
        }}
        .chat-input {{
            flex: 1;
            padding: 12px 15px;
            border: none;
            border-radius: 8px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-size: 14px;
        }}
        .chat-input:focus {{
            outline: 2px solid #6366f1;
        }}
        .chat-input::placeholder {{
            color: #888;
        }}
        .chat-send {{
            padding: 12px 25px;
            border: none;
            border-radius: 8px;
            background: #6366f1;
            color: #fff;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }}
        .chat-send:hover {{
            background: #4f46e5;
        }}
        .chat-send:disabled {{
            background: #4a4a6a;
            cursor: not-allowed;
        }}
        .chat-note {{
            font-size: 12px;
            color: #888;
            margin-top: 10px;
            text-align: center;
        }}
        .typing-indicator {{
            display: none;
            padding: 10px 15px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            max-width: 80%;
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

        /* Navigation */
        .nav-links {{
            display: flex;
            gap: 15px;
            margin-top: 20px;
        }}
        .nav-link {{
            padding: 10px 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
            color: #a5b4fc;
            text-decoration: none;
            transition: background 0.2s;
        }}
        .nav-link:hover {{
            background: rgba(255,255,255,0.2);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Mimir</h1>
        <p class="subtitle">Intelligent Home Assistant Agent with Nordic Wisdom</p>

        <div class="card">
            <h2>Status</h2>
            <div class="status-item">
                <span>Version</span>
                <span>{version}</span>
            </div>
            <div class="status-item">
                <span>LLM Provider</span>
                <span>{llm_provider}</span>
            </div>
            <div class="status-item">
                <span>LLM Model</span>
                <span>{llm_model}</span>
            </div>
            <div class="status-item">
                <span>Operating Mode</span>
                <span>{operating_mode}</span>
            </div>
            <div class="status-item">
                <span>Home Assistant</span>
                <span class="{ha_status_class}">{ha_status}</span>
            </div>
            <div class="status-item">
                <span>WebSocket</span>
                <span class="{ws_status_class}">{ws_status}</span>
            </div>
            <div class="status-item">
                <span>Registered Tools</span>
                <span>{tool_count}</span>
            </div>
        </div>

        <div class="card">
            <h2>Chat with Mimir</h2>
            <div class="chat-container">
                <div class="chat-messages" id="chatMessages">
                    <!-- Messages will be inserted here -->
                </div>
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
            <p class="chat-note">This chat shares history with your Telegram conversation.</p>
        </div>

        <div class="nav-links">
            <a href="/audit" class="nav-link">View Audit Logs</a>
            <a href="/git" class="nav-link">Git History</a>
        </div>
    </div>

    <script>
        // Simple markdown-like formatting
        function formatMessage(text) {{
            // Code blocks
            text = text.replace(/```([\\s\\S]*?)```/g, '<pre>$1</pre>');
            // Inline code
            text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
            // Bold
            text = text.replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>');
            // Line breaks
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
            const indicator = document.getElementById('typingIndicator');
            indicator.className = 'typing-indicator' + (visible ? ' visible' : '');
        }}

        async function sendMessage() {{
            const input = document.getElementById('chatInput');
            const btn = document.getElementById('sendBtn');
            const message = input.value.trim();

            if (!message) return;

            // Add user message
            addMessage('user', message);
            input.value = '';
            btn.disabled = true;
            setTyping(true);

            try {{
                const response = await fetch('/api/chat', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ message: message }})
                }});

                const data = await response.json();

                if (data.error) {{
                    addMessage('assistant', 'Error: ' + data.error);
                }} else {{
                    addMessage('assistant', data.response);
                }}
            }} catch (error) {{
                addMessage('assistant', 'Error: Failed to connect to server');
            }}

            btn.disabled = false;
            setTyping(false);
            input.focus();
        }}

        // Load initial history
        async function loadHistory() {{
            try {{
                const response = await fetch('/api/chat/history');
                const data = await response.json();

                if (data.history) {{
                    data.history.forEach(msg => addMessage(msg.role, msg.content));
                }}
            }} catch (error) {{
                console.error('Failed to load history:', error);
            }}
        }}

        // Load history on page load
        loadHistory();
    </script>
</body>
</html>
"""

# Audit log page
AUDIT_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Audit Logs - Mimir</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        h1 {{
            color: #6366f1;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .back-link {{
            font-size: 14px;
            color: #a5b4fc;
            text-decoration: none;
        }}
        .card {{
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }}
        .filters {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }}
        .filter-select, .filter-input {{
            padding: 8px 12px;
            border: none;
            border-radius: 6px;
            background: rgba(255,255,255,0.1);
            color: #fff;
        }}
        .filter-btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            background: #6366f1;
            color: #fff;
            cursor: pointer;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        th {{ color: #a5b4fc; }}
        tr:hover {{ background: rgba(255,255,255,0.05); }}
        .badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .badge-telegram {{ background: #0088cc; }}
        .badge-web {{ background: #6366f1; }}
        .badge-user {{ background: #22c55e; }}
        .badge-assistant {{ background: #f59e0b; }}
        .badge-tool {{ background: #ef4444; }}
        .content-preview {{
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .pagination {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 20px;
        }}
        .pagination button {{
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            cursor: pointer;
        }}
        .pagination button:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        .detail-modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            padding: 20px;
            overflow-y: auto;
        }}
        .detail-modal.visible {{ display: block; }}
        .detail-content {{
            max-width: 800px;
            margin: 50px auto;
            background: #1a1a2e;
            border-radius: 10px;
            padding: 20px;
        }}
        .detail-close {{
            float: right;
            font-size: 24px;
            cursor: pointer;
            color: #888;
        }}
        .detail-pre {{
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            white-space: pre-wrap;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>
            Audit Logs
            <a href="/" class="back-link">Back to Dashboard</a>
        </h1>

        <div class="card">
            <div class="filters">
                <select class="filter-select" id="filterSource">
                    <option value="">All Sources</option>
                    <option value="telegram">Telegram</option>
                    <option value="web">Web</option>
                </select>
                <select class="filter-select" id="filterType">
                    <option value="">All Types</option>
                    <option value="user">User</option>
                    <option value="assistant">Assistant</option>
                    <option value="tool">Tool</option>
                </select>
                <input type="text" class="filter-input" id="filterSearch" placeholder="Search...">
                <button class="filter-btn" onclick="applyFilters()">Filter</button>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Source</th>
                        <th>Type</th>
                        <th>Content</th>
                    </tr>
                </thead>
                <tbody id="logsTable">
                    <!-- Logs will be inserted here -->
                </tbody>
            </table>

            <div class="pagination">
                <button id="prevBtn" onclick="prevPage()" disabled>Previous</button>
                <span id="pageInfo">Page 1</span>
                <button id="nextBtn" onclick="nextPage()">Next</button>
            </div>
        </div>
    </div>

    <div class="detail-modal" id="detailModal">
        <div class="detail-content">
            <span class="detail-close" onclick="closeDetail()">&times;</span>
            <h2>Log Details</h2>
            <div id="detailBody"></div>
        </div>
    </div>

    <script>
        let currentPage = 0;
        const pageSize = 20;

        function formatTime(timestamp) {{
            const date = new Date(timestamp);
            return date.toLocaleString();
        }}

        function getBadgeClass(type) {{
            const classes = {{
                'telegram': 'badge-telegram',
                'web': 'badge-web',
                'user': 'badge-user',
                'assistant': 'badge-assistant',
                'tool': 'badge-tool'
            }};
            return classes[type] || '';
        }}

        async function loadLogs() {{
            const source = document.getElementById('filterSource').value;
            const type = document.getElementById('filterType').value;
            const search = document.getElementById('filterSearch').value;

            let url = `/api/audit?limit=${{pageSize}}&offset=${{currentPage * pageSize}}`;
            if (source) url += `&source=${{source}}`;
            if (type) url += `&type=${{type}}`;
            if (search) url += `&search=${{encodeURIComponent(search)}}`;

            try {{
                const response = await fetch(url);
                const data = await response.json();

                const tbody = document.getElementById('logsTable');
                tbody.innerHTML = '';

                data.logs.forEach(log => {{
                    const tr = document.createElement('tr');
                    tr.onclick = () => showDetail(log.id);
                    tr.style.cursor = 'pointer';
                    tr.innerHTML = `
                        <td>${{formatTime(log.timestamp)}}</td>
                        <td><span class="badge ${{getBadgeClass(log.source)}}">${{log.source}}</span></td>
                        <td><span class="badge ${{getBadgeClass(log.message_type)}}">${{log.message_type}}</span></td>
                        <td class="content-preview">${{log.content.substring(0, 100)}}</td>
                    `;
                    tbody.appendChild(tr);
                }});

                document.getElementById('pageInfo').textContent = `Page ${{currentPage + 1}}`;
                document.getElementById('prevBtn').disabled = currentPage === 0;
                document.getElementById('nextBtn').disabled = data.logs.length < pageSize;
            }} catch (error) {{
                console.error('Failed to load logs:', error);
            }}
        }}

        async function showDetail(id) {{
            try {{
                const response = await fetch(`/api/audit/${{id}}`);
                const log = await response.json();

                let html = `
                    <p><strong>Timestamp:</strong> ${{formatTime(log.timestamp)}}</p>
                    <p><strong>Source:</strong> ${{log.source}}</p>
                    <p><strong>Type:</strong> ${{log.message_type}}</p>
                    <p><strong>User ID:</strong> ${{log.user_id || 'N/A'}}</p>
                    <h3>Content</h3>
                    <pre class="detail-pre">${{log.content}}</pre>
                `;

                if (log.tool_executions && log.tool_executions.length > 0) {{
                    html += '<h3>Tool Executions</h3>';
                    log.tool_executions.forEach(tool => {{
                        html += `
                            <div class="card">
                                <p><strong>Tool:</strong> ${{tool.tool_name}}</p>
                                <p><strong>Duration:</strong> ${{tool.duration_ms}}ms</p>
                                <p><strong>Success:</strong> ${{tool.success ? 'Yes' : 'No'}}</p>
                                <p><strong>Parameters:</strong></p>
                                <pre class="detail-pre">${{JSON.stringify(tool.parameters, null, 2)}}</pre>
                                <p><strong>Result:</strong></p>
                                <pre class="detail-pre">${{tool.result || 'N/A'}}</pre>
                            </div>
                        `;
                    }});
                }}

                document.getElementById('detailBody').innerHTML = html;
                document.getElementById('detailModal').classList.add('visible');
            }} catch (error) {{
                console.error('Failed to load detail:', error);
            }}
        }}

        function closeDetail() {{
            document.getElementById('detailModal').classList.remove('visible');
        }}

        function applyFilters() {{
            currentPage = 0;
            loadLogs();
        }}

        function prevPage() {{
            if (currentPage > 0) {{
                currentPage--;
                loadLogs();
            }}
        }}

        function nextPage() {{
            currentPage++;
            loadLogs();
        }}

        // Load logs on page load
        loadLogs();
    </script>
</body>
</html>
"""

# Git history page
GIT_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Git History - Mimir</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        h1 {{
            color: #6366f1;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .back-link {{
            font-size: 14px;
            color: #a5b4fc;
            text-decoration: none;
        }}
        .card {{
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }}
        .branch-bar {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            align-items: center;
        }}
        .branch-select {{
            padding: 8px 12px;
            border: none;
            border-radius: 6px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            min-width: 150px;
        }}
        .btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            background: #6366f1;
            color: #fff;
            cursor: pointer;
        }}
        .btn:hover {{ background: #4f46e5; }}
        .btn-danger {{
            background: #ef4444;
        }}
        .btn-danger:hover {{ background: #dc2626; }}
        .commit {{
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }}
        .commit-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 10px;
        }}
        .commit-sha {{
            font-family: monospace;
            color: #6366f1;
            font-size: 12px;
        }}
        .commit-message {{
            font-weight: 500;
            margin-bottom: 5px;
        }}
        .commit-meta {{
            font-size: 12px;
            color: #888;
        }}
        .commit-actions {{
            display: flex;
            gap: 8px;
        }}
        .commit-actions button {{
            padding: 5px 10px;
            font-size: 12px;
        }}
        .diff-view {{
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
            font-family: monospace;
            font-size: 12px;
            overflow-x: auto;
            white-space: pre;
            display: none;
        }}
        .diff-view.visible {{ display: block; }}
        .diff-add {{ color: #22c55e; }}
        .diff-remove {{ color: #ef4444; }}
        .diff-header {{ color: #6366f1; }}
        .no-commits {{
            text-align: center;
            color: #888;
            padding: 40px;
        }}
        .status-bar {{
            padding: 10px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        .status-bar.clean {{ border-left: 4px solid #22c55e; }}
        .status-bar.dirty {{ border-left: 4px solid #f59e0b; }}
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            padding: 20px;
        }}
        .modal.visible {{ display: flex; align-items: center; justify-content: center; }}
        .modal-content {{
            background: #1a1a2e;
            border-radius: 10px;
            padding: 20px;
            max-width: 400px;
            width: 100%;
        }}
        .modal-content h3 {{ margin-top: 0; }}
        .modal-input {{
            width: 100%;
            padding: 10px;
            border: none;
            border-radius: 6px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            margin: 10px 0;
        }}
        .modal-buttons {{
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>
            Configuration History
            <a href="/" class="back-link">Back to Dashboard</a>
        </h1>

        <div class="card">
            <div id="statusBar" class="status-bar clean">
                Loading status...
            </div>

            <div class="branch-bar">
                <select class="branch-select" id="branchSelect" onchange="switchBranch()">
                    <option>Loading...</option>
                </select>
                <button class="btn" onclick="showNewBranchModal()">New Branch</button>
            </div>

            <h2>Commits</h2>
            <div id="commits">
                <div class="no-commits">Loading commits...</div>
            </div>
        </div>
    </div>

    <div class="modal" id="newBranchModal">
        <div class="modal-content">
            <h3>Create New Branch</h3>
            <input type="text" class="modal-input" id="newBranchName" placeholder="Branch name">
            <div class="modal-buttons">
                <button class="btn" onclick="closeModal()">Cancel</button>
                <button class="btn" onclick="createBranch()">Create</button>
            </div>
        </div>
    </div>

    <div class="modal" id="rollbackModal">
        <div class="modal-content">
            <h3>Confirm Rollback</h3>
            <p>Are you sure you want to rollback to commit <code id="rollbackSha"></code>?</p>
            <p style="color: #f59e0b;">This will create a new commit reverting all changes since that commit.</p>
            <div class="modal-buttons">
                <button class="btn" onclick="closeModal()">Cancel</button>
                <button class="btn btn-danger" onclick="confirmRollback()">Rollback</button>
            </div>
        </div>
    </div>

    <script>
        let currentRollbackSha = null;

        function formatDate(dateStr) {{
            return new Date(dateStr).toLocaleString();
        }}

        function formatDiff(diff) {{
            return diff.split('\\n').map(line => {{
                if (line.startsWith('+') && !line.startsWith('+++')) {{
                    return `<span class="diff-add">${{escapeHtml(line)}}</span>`;
                }} else if (line.startsWith('-') && !line.startsWith('---')) {{
                    return `<span class="diff-remove">${{escapeHtml(line)}}</span>`;
                }} else if (line.startsWith('@@') || line.startsWith('diff') || line.startsWith('index')) {{
                    return `<span class="diff-header">${{escapeHtml(line)}}</span>`;
                }}
                return escapeHtml(line);
            }}).join('\\n');
        }}

        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}

        async function loadStatus() {{
            try {{
                const response = await fetch('/api/git/status');
                const data = await response.json();

                const statusBar = document.getElementById('statusBar');
                if (data.clean) {{
                    statusBar.className = 'status-bar clean';
                    statusBar.textContent = 'Working directory clean - no uncommitted changes';
                }} else {{
                    statusBar.className = 'status-bar dirty';
                    statusBar.textContent = `${{data.changed_files || 0}} file(s) with uncommitted changes`;
                }}
            }} catch (error) {{
                console.error('Failed to load status:', error);
            }}
        }}

        async function loadBranches() {{
            try {{
                const response = await fetch('/api/git/branches');
                const data = await response.json();

                const select = document.getElementById('branchSelect');
                select.innerHTML = data.branches.map(b =>
                    `<option value="${{b.name}}" ${{b.current ? 'selected' : ''}}>${{b.name}}${{b.current ? ' (current)' : ''}}</option>`
                ).join('');
            }} catch (error) {{
                console.error('Failed to load branches:', error);
            }}
        }}

        async function loadCommits() {{
            try {{
                const response = await fetch('/api/git/commits?limit=20');
                const data = await response.json();

                const container = document.getElementById('commits');

                if (!data.commits || data.commits.length === 0) {{
                    container.innerHTML = '<div class="no-commits">No commits found</div>';
                    return;
                }}

                container.innerHTML = data.commits.map(commit => `
                    <div class="commit">
                        <div class="commit-header">
                            <div>
                                <div class="commit-message">${{escapeHtml(commit.message)}}</div>
                                <div class="commit-meta">${{commit.author}} - ${{formatDate(commit.date)}}</div>
                                <div class="commit-sha">${{commit.sha}}</div>
                            </div>
                            <div class="commit-actions">
                                <button class="btn" onclick="toggleDiff('${{commit.sha}}')">View Diff</button>
                                <button class="btn btn-danger" onclick="showRollbackModal('${{commit.sha}}')">Rollback</button>
                            </div>
                        </div>
                        <div class="diff-view" id="diff-${{commit.sha}}"></div>
                    </div>
                `).join('');
            }} catch (error) {{
                container.innerHTML = '<div class="no-commits">Failed to load commits</div>';
                console.error('Failed to load commits:', error);
            }}
        }}

        async function toggleDiff(sha) {{
            const diffView = document.getElementById(`diff-${{sha}}`);

            if (diffView.classList.contains('visible')) {{
                diffView.classList.remove('visible');
                return;
            }}

            try {{
                const response = await fetch(`/api/git/diff/${{sha}}`);
                const data = await response.json();

                diffView.innerHTML = formatDiff(data.diff || 'No changes');
                diffView.classList.add('visible');
            }} catch (error) {{
                diffView.innerHTML = 'Failed to load diff';
                diffView.classList.add('visible');
            }}
        }}

        async function switchBranch() {{
            const branch = document.getElementById('branchSelect').value;
            try {{
                await fetch('/api/git/checkout', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ branch: branch }})
                }});
                loadCommits();
                loadStatus();
            }} catch (error) {{
                alert('Failed to switch branch');
            }}
        }}

        function showNewBranchModal() {{
            document.getElementById('newBranchModal').classList.add('visible');
            document.getElementById('newBranchName').value = '';
        }}

        function showRollbackModal(sha) {{
            currentRollbackSha = sha;
            document.getElementById('rollbackSha').textContent = sha.substring(0, 8);
            document.getElementById('rollbackModal').classList.add('visible');
        }}

        function closeModal() {{
            document.querySelectorAll('.modal').forEach(m => m.classList.remove('visible'));
        }}

        async function createBranch() {{
            const name = document.getElementById('newBranchName').value.trim();
            if (!name) return;

            try {{
                await fetch('/api/git/branches', {{
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
                const response = await fetch('/api/git/rollback', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ sha: currentRollbackSha }})
                }});

                if (response.ok) {{
                    closeModal();
                    loadCommits();
                    loadStatus();
                    alert('Rollback successful');
                }} else {{
                    const data = await response.json();
                    alert('Rollback failed: ' + (data.error || 'Unknown error'));
                }}
            }} catch (error) {{
                alert('Failed to rollback: ' + error.message);
            }}
        }}

        // Load on page start
        loadStatus();
        loadBranches();
        loadCommits();
    </script>
</body>
</html>
"""
