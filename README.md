# Mímir

**Intelligent Home Assistant Agent with Nordic Wisdom**

> **⚠️ ALPHA SOFTWARE**
>
> Mímir is in active development. Features may be incomplete, APIs may change, and bugs are expected.
> Use at your own risk on non-production Home Assistant instances. Please report issues on GitHub.

Mímir is an AI-powered agent that interfaces with Home Assistant to manage automations, analyze logs, and provide technical guidance. Named after the Norse god of wisdom, Mímir maintains version control of all modifications and remembers your preferences across sessions.

## Features

### ✅ Implemented

- **Automation Management**: Create, modify, delete, and inspect automations
- **Script Management**: Create, modify, delete scripts
- **Scene Management**: Create, modify, delete scenes
- **Helper Management**: Create and manage input helpers (boolean, number, text, select, counter)
- **Log Analysis**: Analyze Home Assistant error logs and entity history
- **Version Control**: Automatic Git commits for all configuration changes with rollback support
- **Multi-Interface**: Communicate via Telegram or the built-in Home Assistant sidebar panel
- **Long-term Memory**: Mímir remembers facts you tell it across restarts
- **User Context**: Knows who it's talking to and adapts to preferences
- **Web Research**: Search Home Assistant docs, forums, and HACS for solutions
- **Audit Trail**: Full logging of all conversations and tool executions

### ✅ Also Implemented

- **LLM Providers**: Anthropic Claude and OpenAI GPT
- **Rate Limiting**: Configurable limits on destructive actions per hour

### 🚧 Planned / In Progress

- **Additional LLM Providers**: Google Gemini, Azure AI, Ollama, vLLM
- **Operating Mode Enforcement**: Chat/Normal/YOLO mode restrictions

## Installation

### As Home Assistant Add-on

1. Add this repository to your Home Assistant Add-on Store:
   ```
   https://github.com/tobiasritscher/mimir-homeassistant-ai-builder/
   ```
2. Install the Mímir add-on
3. Configure your LLM API key and Telegram settings
4. Start the add-on

### Configuration

```yaml
llm_provider: anthropic           # 'anthropic' or 'openai'
llm_api_key: your-api-key         # Your API key
llm_model: claude-sonnet-4-20250514  # Or gpt-4o for OpenAI
telegram_owner_id: 123456789      # Your Telegram user ID
operating_mode: normal            # chat, normal, or yolo
deletions_per_hour: 5             # Rate limit for deletions
modifications_per_hour: 20        # Rate limit for modifications
debug: false
```

See [DOCS.md](mimir/DOCS.md) for full configuration options.

## Usage

### Telegram Commands

Send messages to your Mímir Telegram bot:

- "Create an automation that turns off all lights at midnight"
- "Why does the garage door automation keep failing?"
- "Analyze recent errors in the logs"
- "Enable YOLO mode" (auto-approve all actions for 10 minutes)

### Operating Modes

- **Chat Mode**: Read-only analysis and recommendations
- **Normal Mode**: Some actions auto-approved, others require confirmation
- **YOLO Mode**: All actions auto-approved (time-limited)

## Development

### Requirements

- Python 3.11+
- Home Assistant with MCP Server and Telegram Bot integrations

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/mimir.git
cd mimir

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
mypy .
```

## Architecture

Mímir is built as a Home Assistant add-on with the following components:

- **LLM Abstraction Layer**: Unified interface for multiple LLM providers
- **MCP Client**: Connects to Home Assistant's MCP Server integration
- **Telegram Handler**: Listens to HA's telegram_bot events
- **Conversation Manager**: Maintains context and orchestrates agent actions
- **Tools Framework**: Extensible tools for web search, HA operations, etc.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting PRs.

## Acknowledgments

- Named after Mímir from Norse mythology, keeper of the well of wisdom
- Personality inspired by the God of War (2018/Ragnarök) characterization
