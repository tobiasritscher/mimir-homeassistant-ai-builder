# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
