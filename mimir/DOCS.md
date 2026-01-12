# Mímir - Documentation

Mímir is an intelligent AI agent that interfaces with Home Assistant to manage automations, scripts, scenes, helpers, and perform log analysis. Named after the Norse god of wisdom, Mímir provides technical guidance while maintaining version control of all modifications.

> **Note**: Mímir is alpha software. Features may change and bugs are expected.

## Table of Contents

- [Configuration](#configuration)
- [Web Interface](#web-interface)
- [Capabilities](#capabilities)
- [Tools Reference](#tools-reference)
- [Memory System](#memory-system)
- [Rate Limiting](#rate-limiting)
- [Git Integration](#git-integration)
- [Troubleshooting](#troubleshooting)

## Configuration

All configuration is done through the Home Assistant Add-on configuration page.

### LLM Provider

| Provider | Status | Models |
|----------|--------|--------|
| `anthropic` | Supported | claude-sonnet-4-20250514, claude-3-5-haiku-20241022 |
| `openai` | Supported | gpt-4o, gpt-4-turbo, gpt-3.5-turbo |
| `gemini` | Supported | gemini-1.5-pro, gemini-1.5-flash |
| `azure` | Supported | Azure OpenAI models (requires base_url) |
| `ollama` | Supported | llama3.2, mistral, codellama, etc. |
| `vllm` | Supported | Any model served by vLLM |

### LLM API Key

Your API key for the selected provider. This is stored securely in Home Assistant and never exposed.

- **Anthropic**: Get your key at https://console.anthropic.com/
- **OpenAI**: Get your key at https://platform.openai.com/api-keys

### LLM Model

The specific model to use. Recommended defaults:

- **Anthropic**: `claude-sonnet-4-20250514` (best balance of quality and cost)
- **OpenAI**: `gpt-4o` (best quality) or `gpt-4-turbo` (faster)

### LLM Base URL (Optional)

For custom API endpoints (Azure, self-hosted, etc.). Leave empty for standard endpoints.

### Telegram Owner ID

Your Telegram user ID. Mímir only responds to messages from this ID for security.

**How to find your ID:**
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will reply with your user ID

### Operating Mode

| Mode | Description |
|------|-------------|
| `chat` | Read-only. Mímir can analyze and recommend but cannot make changes. All write tools are blocked. |
| `normal` | Default. Read operations auto-approved. Destructive operations require confirmation. |
| `yolo` | All actions auto-approved for a limited duration. Use with caution! |

**Mode Switching Commands:**
- "enable chat mode" / "switch to chat mode"
- "enable normal mode" / "switch to normal mode"
- "enable yolo mode" / "switch to yolo mode"
- "what mode am I in?" / "current mode"

### Rate Limits

Protect against runaway modifications:

| Setting | Default | Description |
|---------|---------|-------------|
| `deletions_per_hour` | 5 | Maximum deletions in a sliding 1-hour window |
| `modifications_per_hour` | 20 | Maximum creates/updates in a sliding 1-hour window |

### Git Integration

| Setting | Default | Description |
|---------|---------|-------------|
| `git_enabled` | true | Enable automatic version control |
| `git_author_name` | Mímir | Name for commit messages |
| `git_author_email` | mimir@asgard.local | Email for commit messages |

### Debug Mode

Set `debug: true` for verbose logging. Useful for troubleshooting.

## Web Interface

Access Mímir through the Home Assistant sidebar (click the Mímir icon).

### Available Pages

| Page | Path | Description |
|------|------|-------------|
| Chat | `/` | Main chat interface |
| Status | `/status` | System status and connection info |
| Audit | `/audit` | View all conversations and tool executions |
| Git History | `/git` | View commits, diffs, and rollback |
| Debug | `/debug` | View request headers and user context |

### Chat Interface

The chat interface provides:
- Full conversation with Mímir
- Quick action buttons for common tasks
- Message history across sessions
- User context awareness (knows who you are)

## Capabilities

### What Mímir Can Do

**Automation Management**
- List all automations with status
- View full automation configuration
- Create new automations
- Update existing automations
- Delete automations
- Enable/disable automations

**Script Management**
- List all scripts
- View script configuration
- Create/update/delete scripts
- Run scripts

**Scene Management**
- List all scenes
- View scene configuration
- Create/update/delete scenes
- Activate scenes

**Helper Management**
- List input helpers (boolean, number, text, select, datetime, counter, timer)
- Create new helpers
- Delete helpers
- Set helper values

**Entity Operations**
- List entities by domain or search
- Get detailed entity state
- Call services on entities

**Log Analysis**
- Get Home Assistant error log
- Get logbook entries for entities
- Analyze and explain errors

**Web Research**
- Search Home Assistant documentation
- Search community forums
- Search HACS repositories

**Long-term Memory**
- Remember facts you tell it
- Recall relevant memories
- Forget outdated information

### What Mímir Cannot Do

- Modify network configuration
- Manage users or permissions
- Handle SSL/certificates
- Install add-ons or integrations directly
- Access external systems

## Tools Reference

### Entity Tools

| Tool | Description |
|------|-------------|
| `get_entities` | List entities, filter by domain or search |
| `get_entity_state` | Get detailed state of an entity |
| `call_service` | Call a Home Assistant service |
| `get_services` | List available services in a domain |
| `rename_entity` | Change an entity's friendly name |
| `assign_entity_area` | Assign an entity to an area |
| `assign_entity_labels` | Assign labels to an entity |
| `get_areas` | List all defined areas |
| `get_labels` | List all defined labels |

### Automation Tools

| Tool | Description |
|------|-------------|
| `get_automations` | List all automations with status |
| `get_automation_config` | Get full YAML config of an automation |
| `create_automation` | Create a new automation |
| `update_automation` | Update an existing automation |
| `delete_automation` | Delete an automation |

### Script Tools

| Tool | Description |
|------|-------------|
| `get_scripts` | List all scripts |
| `get_script_config` | Get full config of a script |
| `create_script` | Create a new script |
| `update_script` | Update an existing script |
| `delete_script` | Delete a script |

### Scene Tools

| Tool | Description |
|------|-------------|
| `get_scenes` | List all scenes |
| `get_scene_config` | Get full config of a scene |
| `create_scene` | Create a new scene |
| `update_scene` | Update an existing scene |
| `delete_scene` | Delete a scene |

### Helper Tools

| Tool | Description |
|------|-------------|
| `get_helpers` | List all input helpers |
| `create_helper` | Create a new helper |
| `delete_helper` | Delete a helper |

### Log Tools

| Tool | Description |
|------|-------------|
| `get_error_log` | Get Home Assistant error log |
| `get_logbook` | Get recent logbook entries |

### Memory Tools

| Tool | Description |
|------|-------------|
| `store_memory` | Save a fact permanently |
| `recall_memories` | Search stored memories |
| `forget_memory` | Delete a stored memory |

### Web Search Tools

| Tool | Description |
|------|-------------|
| `web_search` | General web search |
| `ha_docs_search` | Search Home Assistant docs |
| `hacs_search` | Search HACS repositories |

## Memory System

Mímir can remember facts across sessions. Use phrases like:

- "Remember that the kitchen motion sensor is binary_sensor.kitchen_motion"
- "Note that I prefer lights at 50% brightness"
- "Store that the guest room is actually my office now"

To recall: "What do you remember about the kitchen?"

To forget: "Forget about the kitchen motion sensor"

### Memory Categories

- `user_preference` - User preferences and settings
- `device_info` - Device names, locations, entity IDs
- `automation_note` - Notes about automations
- `home_layout` - Room and area information
- `routine` - Daily routines and schedules
- `general` - Other facts

## Rate Limiting

Rate limits protect against:
- Accidental bulk deletions
- Runaway automation loops
- API cost overruns

When a limit is hit, Mímir will inform you and refuse the operation until the window passes.

**Reset:** Rate limits use a sliding 1-hour window. Wait for older operations to "age out."

**YOLO Mode:** Disables rate limiting temporarily. Use with extreme caution.

## Git Integration

When enabled, Mímir:
1. Creates a `.gitignore` for sensitive files
2. Commits configuration changes automatically
3. Tracks history at `/git` endpoint
4. Allows viewing diffs of any commit
5. Supports rollback to previous states

### Ignored Files

The following are automatically excluded from Git:
- Authentication and tokens (`.storage/auth`, `secrets.yaml`)
- Databases (`*.db`, `home-assistant_v2.db`)
- Logs (`*.log`)
- Frequently changing files (entity registry, restore state, HACS data)
- Cache and temp files

## Troubleshooting

### Common Issues

**"Failed to connect to Home Assistant"**
- Check that the add-on is running
- Verify your Telegram bot is configured in Home Assistant
- Check the add-on logs for errors

**"Rate limit exceeded"**
- Wait for operations to age out of the 1-hour window
- Increase limits in configuration if needed
- Consider if your use case is appropriate

**"Automation/Script not found"**
- UI-created automations have internal IDs
- YAML-defined automations cannot be modified via API
- Check the entity_id is correct

**"Unknown tool" errors**
- This may indicate a version mismatch
- Restart the add-on
- Check for updates

### Getting Help

1. Check this documentation
2. View logs at the `/audit` endpoint
3. Enable `debug: true` for verbose logs
4. Open an issue on [GitHub](https://github.com/tobiasritscher/mimir-homeassistant-ai-builder/issues)

### Debug Endpoint

Visit `/debug` to see:
- Current request headers
- User context (who Mímir thinks you are)
- Ingress path information

## Security Considerations

- API keys are stored securely in Home Assistant
- Telegram messages are only accepted from the configured owner ID
- All operations are logged in the audit trail
- Sensitive files are excluded from Git commits
- Rate limits prevent bulk operations

## Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/tobiasritscher/mimir-homeassistant-ai-builder/issues)
- **Contributing**: See [CONTRIBUTING.md](../CONTRIBUTING.md)
