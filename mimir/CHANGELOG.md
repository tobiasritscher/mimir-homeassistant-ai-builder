# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.43] - 2025-01-12

### Fixed

- Fix mypy type check errors
  - Add explicit type annotations in gemini.py for `parts` and `declaration` variables
  - Add explicit `return None` in conversation/manager.py `_check_mode_command`
  - Convert config.OperatingMode to mode_manager.OperatingMode in main.py

## [0.1.42] - 2025-01-12

### Fixed

- Fix ruff lint and type check errors in CI pipeline
  - Remove unused imports (json, timedelta, OperatingMode, is_write_operation)
  - Remove unused variables (result, now)
  - Fix import sorting in main.py
  - Use ternary operator in gemini.py
  - Use contextlib.suppress in notifications/manager.py
  - Combine nested if statements in mode_manager.py
  - Add noqa comments for intentional type-checking imports
  - Format all files with ruff

## [0.1.41] - 2025-01-12

### Fixed

- Fix startup crash when `openai` module not installed
  - Changed to lazy imports for all LLM providers
  - OpenAI, Gemini, Azure, Ollama, vLLM only imported when selected

## [0.1.40] - 2025-01-12

### Added

- **Operating Mode Enforcement**: Modes now actually control behavior
  - Chat Mode: Read-only, blocks all write operations
  - Normal Mode: Confirmation required for destructive operations
  - YOLO Mode: Auto-approve all with configurable timer
  - Mode switching commands: "enable chat mode", "switch to normal mode", etc.
  - Mode status queries: "what mode am I in?"
  - System prompt includes mode-specific instructions

- **Entity Registry Operations**: New tools for managing entities
  - `rename_entity` - Change entity friendly name
  - `assign_entity_area` - Assign entities to areas
  - `assign_entity_labels` - Assign labels to entities
  - `get_areas` - List all available areas
  - `get_labels` - List all available labels

- **Additional LLM Providers**: Support for more AI backends
  - Google Gemini (gemini-1.5-pro, gemini-1.5-flash)
  - Azure OpenAI (via custom base_url)
  - Ollama (local models like llama3.2, mistral)
  - vLLM (local OpenAI-compatible server)

- **Proactive Notifications**: Automatic issue detection and alerts
  - Monitors error log for critical issues
  - Detects unavailable entities
  - Sends notifications via Telegram
  - Configurable check interval (default: 30 minutes)

### Changed

- Mode manager integrated into tool registry and conversation manager
- System prompt now includes current operating mode with mode-specific instructions

## [0.1.39] - 2025-01-12

### Added

- **Script CRUD tools**: Full management of Home Assistant scripts
  - `get_scripts` - List all scripts with status
  - `get_script_config` - Get full YAML configuration
  - `create_script` - Create new scripts
  - `update_script` - Update existing scripts
  - `delete_script` - Delete scripts

- **Scene CRUD tools**: Full management of scenes
  - `get_scenes` - List all scenes
  - `get_scene_config` - Get scene configuration
  - `create_scene` - Create new scenes
  - `update_scene` - Update existing scenes
  - `delete_scene` - Delete scenes

- **Helper CRUD tools**: Create and manage input helpers
  - `get_helpers` - List all helpers (input_boolean, input_number, etc.)
  - `create_helper` - Create new helpers
  - `delete_helper` - Delete helpers

- **Rate limiting**: Protect against runaway modifications
  - Configurable `deletions_per_hour` (default: 5)
  - Configurable `modifications_per_hour` (default: 20)
  - Sliding 1-hour window tracking
  - Disabled in YOLO mode

- **OpenAI LLM provider**: Support for GPT models
  - GPT-4o, GPT-4-turbo, GPT-3.5-turbo
  - Custom base URL support for Azure/compatible APIs

- **GitHub issue templates**: Bug reports and feature requests

- **Expanded documentation**: Comprehensive DOCS.md with all features

- **CONTRIBUTING.md**: Guidelines for contributors

### Changed

- **README.md**: Added alpha warning, documented implemented vs planned features
- **HA_GITIGNORE**: Expanded to cover more noisy/sensitive files
  - Added `cloud/`, `www/community/`, `zigbee2mqtt/` patterns
  - Added more `.storage/` entries

## [0.1.38] - 2025-01-11

### Added

- **User context awareness**: Mímir now knows who it's talking to
  - Extracts user info from Home Assistant ingress headers (X-Remote-User-*)
  - Includes user's display name and username in system prompt
  - Works for both web (HA sidebar) and Telegram users
  - Debug endpoint (`/debug`) shows extracted user context
  - Enables personalized responses based on user preferences

## [0.1.37] - 2025-01-11

### Fixed

- **Proper ingress support for API calls**
  - Use `X-Ingress-Path` header to determine base URL for API requests
  - All fetch calls now use `apiUrl()` helper with the correct ingress path
  - Fixes 404 errors when using chat via Home Assistant sidebar panel

## [0.1.36] - 2025-01-11

### Fixed

- Fix 404 errors on API calls in ingress context
  - Changed all API fetch URLs from `api/` to `./api/`
  - Ensures proper relative URL resolution when served through HA ingress proxy

## [0.1.35] - 2025-01-11

### Fixed

- Better error handling for chat API calls
  - Check response.ok before parsing JSON
  - Show HTTP status code and response text on error

## [0.1.34] - 2025-01-11

### Fixed

- Fix mypy type errors in templates.py

## [0.1.33] - 2025-01-11

### Fixed

- Show actual error message in chat instead of generic "Failed to connect"

## [0.1.32] - 2025-01-11

### Changed

- Reverted to original polished chat UI design
- Kept `/debug` endpoint and INFO-level request logging for diagnostics

## [0.1.31] - 2025-01-11

### Changed

- Simplified chat page for ingress testing (reverted in 0.1.32)

## [0.1.30] - 2025-01-11

### Added

- **Proper .gitignore for Home Assistant config**
  - Excludes sensitive files (auth tokens, secrets.yaml, certificates)
  - Excludes noisy files (sensor data, logs, databases, backups)
  - Auto-created on git initialization
  - Cleans up already-tracked ignored files from existing repos

## [0.1.29] - 2025-01-11

### Changed

- **Chat is now the default view** for ingress panel
  - Fixes ingress double-slash path issue (`//`) that caused HA dashboard to show
  - Status/dashboard page moved to `/status`
  - Navigation links updated across all pages
  - Explicit `//` route handler added as fallback

## [0.1.28] - 2025-01-11

### Fixed

- fixed Dashboard versioning

## [0.1.27] - 2025-01-11

### Added

- fixed side pannel (hopefully)

## [0.1.26] - 2025-01-11

### Added

- added new Icon

## [0.1.25] - 2025-01-11

### Fixed

- Fix ingress panel opening HA dashboard instead of Mímir
  - Changed from redirect (301) to request cloning
  - Redirect broke ingress because browser interpreted `/` as HA root
  - Now normalizes path in-place without redirect

## [0.1.24] - 2025-01-11

### Fixed

- Fix 404 error on ingress panel access
  - Added `normalize_path_middleware` to handle trailing slashes
  - Improved request logging with X-Ingress-Path header

## [0.1.23] - 2025-01-11

### Added

- **Long-term memory system**: Mímir can now remember facts permanently
  - New `store_memory` tool: Save facts when user says "merke dir das"
  - New `recall_memories` tool: Search stored memories
  - New `forget_memory` tool: Delete outdated memories
  - Categories: user_preference, device_info, automation_note, home_layout, routine, general
  - Memories are included in system prompt for every conversation
  - Persists across restarts in SQLite database

## [0.1.22] - 2025-01-11

### Added

- **Conversation memory persistence**: Mímir now remembers conversations after restarts
  - Loads recent conversation history from audit database on startup
  - Context is preserved across add-on updates and restarts
  - No more "I don't have access to previous conversations" responses

## [0.1.21] - 2025-01-11

### Fixed

- Fix service calls not working (API problem)
  - `call_service` was wrapping target in nested object: `{"target": {"entity_id": ...}}`
  - HA REST API expects `entity_id` directly in payload: `{"entity_id": ...}`
  - Now correctly merges target into service data

## [0.1.20] - 2025-01-10

### Added

- Request logging middleware for debugging ingress issues
  - Logs all incoming HTTP requests with path and headers
  - Logs response status codes
  - Helps diagnose 404/503 errors with ingress

## [0.1.19] - 2025-01-10

### Added

- **Commit button** on Git history page
  - "Commit All" button appears when there are uncommitted changes
  - Auto-generates meaningful commit messages based on what changed:
    - Categorizes changes (automations, scripts, core config, other)
    - Shows action type (Add/Update/Remove)
    - Includes file count
  - Shows commit result with message used
  - Automatically refreshes commits list after successful commit

## [0.1.18] - 2025-01-10

### Fixed

- Fix git diff loading hanging forever
  - Added 30-second timeout to all git subprocess commands
  - Large diffs (initial commit with entire /config) now show stats only
  - Diffs over 100KB are truncated with a message
  - Timeout errors are handled gracefully with informative message

## [0.1.17] - 2025-01-10

### Fixed

- Fix "Invalid Date" on Git history page
  - Changed git date format from `%ai` to `%aI` (strict ISO 8601)
  - JavaScript can now parse dates correctly
- Fix diff loading hanging forever
  - Added initialization check to `get_diff()` method

## [0.1.16] - 2025-01-10

### Fixed

- Fix CSS not rendering on Audit, Git, and Chat pages
  - Templates with shared CSS used doubled braces `{{}}` for `.format()` compatibility
  - Pages not using `.format()` were serving invalid CSS with literal `{{` braces
  - Now all page handlers call `.format()` to convert braces properly

## [0.1.15] - 2025-01-10

### Added

- **Ingress support**: "Open Web UI" button now works in Home Assistant add-on page
- **Sidebar integration**: Mímir appears in HA sidebar with `mdi:head-lightbulb` icon
- **Chat-only page**: Simplified chat interface at `/chat` with quick actions
  - Analyze Logs, Recent Changes, Automations, Unavailable Devices buttons
  - Full-height chat interface optimized for focused conversations
  - Welcome screen with suggestion prompts
- Navigation links between Dashboard and Chat views

### Changed

- Dashboard now includes link to chat-only view

## [0.1.14] - 2025-01-10

### Fixed

- Fix dashboard crash caused by CSS brace escaping issue
  - Python's `.format()` method was interpreting CSS `{}` as format placeholders
  - All CSS braces in SHARED_STYLES now properly doubled for escaping

## [0.1.13] - 2025-01-10

### Changed

- Complete redesign of web UI with polished dark theme
  - Glassmorphism-style cards with subtle borders and shadows
  - Gradient buttons with hover effects
  - Custom styled dropdowns and form inputs
  - Color-coded badges for sources and message types
  - Loading spinners and empty state indicators
  - Modal overlays with backdrop blur
  - Git diff viewer with syntax highlighting
  - Smooth animations and transitions throughout

## [0.1.12] - 2025-01-10

### Added

- **Web Chat Interface**: Chat with Mímir directly from the web UI at `/`
  - Shares conversation history with Telegram
  - Real-time message display with typing indicator
- **Audit Logging**: Full audit trail at `/audit`
  - Logs all messages (user, assistant, tool calls)
  - Records tool execution details (parameters, results, duration)
  - Filter by source, type, or search content
- **Git Version Control**: Manage HA config history at `/git`
  - View commit history with diffs
  - Rollback to previous configurations
  - Create and switch branches
- **Automation Preservation**: Mímir now makes minimal, surgical edits
  - Shows diff of proposed changes before applying
  - Preserves existing logic when modifying automations
  - Asks for confirmation on significant changes

### Changed

- Enhanced status page with embedded chat interface
- Database storage at `/data/mimir.db` for audit logs

## [0.1.11] - 2025-01-10

### Fixed

- Automation CRUD tools now correctly use the internal `id` attribute from entity state
  - Previously used entity_id slug which doesn't match the API endpoint requirement
  - Now first fetches entity state to get the internal ID, then uses that for config API
- All automation tools use consistent `entity_id` parameter naming

### Added

- Language matching: Mímir now responds in the same language as the user's message
  - German questions get German answers, English questions get English answers, etc.

## [0.1.10] - 2025-01-10

### Added

- Automation CRUD tools:
  - `get_automation_config` - Get full YAML config of an automation
  - `create_automation` - Create a new automation
  - `update_automation` - Update an existing automation
  - `delete_automation` - Delete an automation
- HA API methods for automation management

## [0.1.9] - 2025-01-10

### Added

- Home Assistant tools for LLM interaction:
  - `get_entities` - List entities, filter by domain or search
  - `get_entity_state` - Get detailed state of a specific entity
  - `get_automations` - List all automations with status
  - `call_service` - Call HA services (turn on/off, etc.)
  - `get_services` - List available services in a domain
  - `get_error_log` - Get HA error log
  - `get_logbook` - Get recent entity history

## [0.1.8] - 2025-01-10

### Added

- Token debugging to find SUPERVISOR_TOKEN source

## [0.1.7] - 2025-01-10

### Fixed

- Revert to simple init: false approach (v0.1.4 style) that was working
- Use internal Docker network (homeassistant:8123) when SUPERVISOR_TOKEN unavailable
- Removed S6 overlay v3 service structure that caused crashes

## [0.1.6] - 2025-01-10

### Changed

- Update base images to Python 3.12 / Alpine 3.20
- Use proper S6 overlay v3 service structure instead of legacy /run.sh
- Add finish script for graceful shutdown handling

## [0.1.5] - 2025-01-10

### Fixed

- Use with-contenv wrapper to get S6 environment variables (SUPERVISOR_TOKEN)
- Remove init: false since S6 is running anyway
- Remove CMD to let S6 handle script execution

## [0.1.4] - 2025-01-10

### Fixed

- Fix Python relative import error by restructuring to /opt/mimir/app/
- Run as module (python -m app.main) instead of script

## [0.1.3] - 2025-01-10

### Fixed

- Bypass S6 overlay completely (init: false) to fix startup crash
- Use plain bash + jq instead of bashio for config reading
- Add CMD back to Dockerfile for non-S6 mode

## [0.1.2] - 2025-01-10

### Added

- Web status interface on port 5000
- Health check endpoint at /health
- HA connection retry logic (5 attempts)

### Fixed

- App no longer exits if HA connection fails initially

## [0.1.1] - 2025-01-10

### Fixed

- Remove restrictive AppArmor profile that blocked S6 overlay init
- Remove CMD override to let S6 overlay handle entrypoint

## [0.1.0] - 2025-01-10

### Added

- Initial release of Mímir
- LLM abstraction layer with Anthropic Claude support
- Home Assistant integration via MCP client and WebSocket
- Telegram integration via HA's telegram_bot events
- Web search tool for documentation and forum research
- Basic conversation management
- Configuration via Home Assistant add-on options
