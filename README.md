# Mímir

**Intelligent Home Assistant Agent with Nordic Wisdom**

Mímir is an AI-powered agent that interfaces with Home Assistant to manage automations, scripts, helpers, scenes, dashboards, and perform log analysis. Named after the Norse god of wisdom, Mímir provides technical guidance with a sardonic wit while maintaining version control of all modifications.

## Features

- **Automation Management**: Create, modify, and delete automations, scripts, scenes, and helpers
- **Log Analysis**: Analyze Home Assistant logs to identify and explain errors
- **Version Control**: Automatic Git commits for all configuration changes
- **Multi-Interface**: Communicate via Telegram or the built-in Home Assistant panel
- **Model Agnostic**: Supports Anthropic Claude, OpenAI, Google Gemini, Azure AI, Ollama, and vLLM
- **Web Research**: Search documentation and forums for solutions

## Installation

### As Home Assistant Add-on

1. Add this repository to your Home Assistant Add-on Store:
   ```
   https://github.com/yourusername/mimir
   ```
2. Install the Mímir add-on
3. Configure your LLM API key and Telegram settings
4. Start the add-on

### Configuration

```yaml
llm_provider: anthropic
llm_api_key: your-api-key
llm_model: claude-sonnet-4-20250514
telegram_owner_id: 123456789
debug: false
```

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

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## Acknowledgments

- Named after Mímir from Norse mythology, keeper of the well of wisdom
- Personality inspired by the God of War (2018/Ragnarök) characterization
