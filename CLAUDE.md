# Mímir - Claude Code Context

## Project Overview

Mímir is a Home Assistant add-on that provides an intelligent AI agent for managing automations, scripts, scenes, helpers, and performing log analysis. Named after the Norse god of wisdom.

## Architecture

```
mimir/
├── app/                    # Main Python application
│   ├── main.py            # Entry point, MimirAgent class
│   ├── config.py          # Configuration loading from HA add-on options
│   ├── conversation/      # LLM conversation management
│   │   └── manager.py     # ConversationManager - orchestrates LLM + tools
│   ├── llm/               # LLM provider abstraction
│   │   ├── base.py        # Abstract LLMProvider interface
│   │   ├── factory.py     # Provider factory (lazy imports!)
│   │   ├── anthropic.py   # Claude provider
│   │   ├── openai.py      # GPT provider
│   │   ├── gemini.py      # Google Gemini provider
│   │   ├── local.py       # Ollama/vLLM providers
│   │   └── types.py       # Message, Response, Tool types
│   ├── ha/                # Home Assistant integration
│   │   ├── api.py         # REST API client
│   │   ├── websocket.py   # WebSocket for events
│   │   └── types.py       # HA-specific types
│   ├── tools/             # LLM tools (function calling)
│   │   ├── base.py        # BaseTool interface
│   │   ├── registry.py    # ToolRegistry with rate limiting
│   │   ├── ha_tools.py    # All HA tools (entities, automations, etc.)
│   │   ├── memory_tools.py # Long-term memory tools
│   │   └── web_search.py  # Web search tools
│   ├── telegram/          # Telegram bot integration
│   ├── web/               # Web UI (aiohttp)
│   ├── git/               # Git version control
│   ├── db/                # SQLite database (audit, memory)
│   ├── notifications/     # Proactive notification system
│   └── utils/             # Utilities
│       ├── mode_manager.py # Operating mode enforcement
│       ├── rate_limiter.py # Rate limiting for tools
│       └── logging.py
├── config.yaml            # HA add-on configuration schema
├── Dockerfile             # Container build
├── requirements.txt       # Python dependencies
├── CHANGELOG.md           # Version history
└── DOCS.md               # User documentation
```

## Key Concepts

### Operating Modes
- **Chat**: Read-only, blocks all write tools
- **Normal**: Confirmation required for destructive operations
- **YOLO**: Auto-approve everything (timed)

Mode enforcement happens in:
1. `utils/mode_manager.py` - Mode state and switching
2. `tools/registry.py` - Blocks tools based on mode
3. `conversation/manager.py` - Includes mode in system prompt

### Tool System
Tools are registered in `main.py._register_tools()`. Each tool:
- Extends `BaseTool`
- Has `name`, `description`, `parameters` properties
- Implements async `execute(**kwargs)` method
- Returns string result

Rate limiting is configured per-tool in `utils/rate_limiter.py`.

### LLM Providers
All providers implement `LLMProvider` interface:
- `complete()` - Single response
- `stream()` - Streaming response
- Must handle tool calls

**Important**: Use lazy imports in `factory.py` to avoid missing module errors.

### Home Assistant Integration
- REST API via `ha/api.py` for most operations
- WebSocket via `ha/websocket.py` for Telegram events
- Entity registry operations require WebSocket (`_ws_command` method)

## Development Guidelines

### Adding a New Tool
1. Create class in `tools/ha_tools.py` (or new file)
2. Extend `BaseTool`, implement required properties
3. Register in `main.py._register_tools()`
4. Add to `TOOL_CATEGORIES` in `utils/mode_manager.py` if write operation
5. Add to `TOOL_OPERATION_TYPES` in `utils/rate_limiter.py` if rate-limited

### Adding a New LLM Provider
1. Create provider in `llm/` directory
2. Implement `LLMProvider` interface
3. Add to `LLMProviderEnum` in `config.py`
4. Add case in `factory.py` with **lazy import**
5. Add dependency to `requirements.txt`

### Version Bumping
Update version in three places:
1. `mimir/app/main.py` - `MimirAgent.VERSION`
2. `mimir/config.yaml` - `version` field
3. `mimir/CHANGELOG.md` - Add new version section

## Common Patterns

### Async Everything
All I/O operations are async. Use `await` consistently.

### Error Handling in Tools
Tools return error strings, don't raise exceptions:
```python
async def execute(self, **kwargs):
    try:
        # ... do work
        return "Success message"
    except Exception as e:
        logger.exception("Failed: %s", e)
        return f"Error: {e}"
```

### Configuration Access
Config loaded once at startup via `config.py.load_config()`. Access via `self._config` in MimirAgent.

## Testing Locally

The add-on runs in a Docker container. For local testing:
1. Set environment variables (SUPERVISOR_TOKEN, etc.)
2. Run with `python -m app.main`

## Important Files to Know

- `main.py` - Start here to understand the flow
- `conversation/manager.py` - Core LLM interaction logic
- `tools/registry.py` - Tool execution with mode/rate enforcement
- `config.yaml` - Add-on options schema (what users configure)

## Release Process

### Pre-Release Checklist

1. **Run Linting** (matches CI `lint` job)
   ```bash
   cd mimir
   ruff check app/
   ruff format --check app/
   ```
   Fix any issues before proceeding.

2. **Run Type Checking** (matches CI `typecheck` job)
   ```bash
   cd mimir
   mypy app/ --ignore-missing-imports
   ```
   Fix any type errors before proceeding.

3. **Run Tests** (matches CI `test` job)
   ```bash
   cd mimir
   pytest tests/ -v
   ```
   All tests must pass.

### Version Bump (all 3 places!)

1. **`mimir/app/main.py`** - Update `MimirAgent.VERSION`:
   ```python
   VERSION = "0.1.42"  # bump this
   ```

2. **`mimir/config.yaml`** - Update `version` field:
   ```yaml
   version: "0.1.42"  # bump this
   ```

3. **`mimir/CHANGELOG.md`** - Add new version section:
   ```markdown
   ## [0.1.42] - YYYY-MM-DD

   ### Added
   - New feature description

   ### Changed
   - Change description

   ### Fixed
   - Bug fix description
   ```

### Commit and Push

```bash
git add -A
git commit -m "$(cat <<'EOF'
v0.1.42: Brief description

- Bullet points for details
- More details

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
git push origin main
```

### Wait for CI

After pushing, wait for GitHub Actions to complete:
- **lint**: ruff check and format
- **typecheck**: mypy
- **test**: pytest
- **build-addon**: Docker build

Check status at: https://github.com/tobiasritscher/mimir-homeassistant-ai-builder/actions

### Home Assistant Add-on Update

Users update the add-on via:
1. Home Assistant → Settings → Add-ons → Mimir
2. Click "Update" if available
3. **Important**: After update, must "Rebuild" not just "Restart" for code changes to take effect

The version shown in HA comes from `config.yaml`. Home Assistant checks for updates by comparing the `version` field against what's installed.

### Post-Release Verification

1. Check add-on logs for startup errors
2. Test chat interface works
3. Verify new features function correctly

## Commit Messages

Follow conventional format:
```
v0.1.XX: Brief description

- Bullet points for details
- More details

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

## CI Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs:

| Job | Command | Purpose |
|-----|---------|---------|
| lint | `ruff check app/` + `ruff format --check app/` | Code style |
| typecheck | `mypy app/ --ignore-missing-imports` | Type safety |
| test | `pytest tests/ -v` | Unit tests |
| build-addon | `docker build` | Verify container builds |

All jobs must pass before merging/deploying.
