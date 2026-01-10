# Mímir - Documentation

Mímir is an intelligent agent that interfaces with Home Assistant to manage automations, scripts, helpers, scenes, dashboards, and perform log analysis.

## Configuration

### LLM Provider

Select your preferred LLM provider. Currently supported:

- **anthropic**: Anthropic Claude (recommended)
- **openai**: OpenAI GPT models (coming soon)
- **gemini**: Google Gemini (coming soon)
- **azure**: Azure AI Foundry (coming soon)
- **ollama**: Local Ollama models (coming soon)
- **vllm**: Local vLLM models (coming soon)

### LLM API Key

Your API key for the selected provider. This is stored securely and never committed to version control.

### LLM Model

The specific model to use. Defaults vary by provider:

- Anthropic: `claude-sonnet-4-20250514`

### Telegram Owner ID

Your Telegram user ID. Mímir will only respond to messages from this user. You can find your ID by messaging @userinfobot on Telegram.

### Operating Mode

- **chat**: Read-only mode. Mímir can analyze and recommend but cannot make changes.
- **normal**: Default mode. Some actions are auto-approved, others require confirmation.
- **yolo**: All actions auto-approved for a limited duration (use with caution).

### Rate Limits

- **deletions_per_hour**: Maximum deletions allowed per hour (default: 5)
- **modifications_per_hour**: Maximum modifications allowed per hour (default: 20)

### Git Integration

When enabled, Mímir automatically commits all configuration changes to a local Git repository for version control and rollback capability.

## Usage

### Telegram

Send messages to your Home Assistant Telegram bot. Example commands:

- "Create an automation that turns off all lights at midnight"
- "Disable the kitchen motion automation"
- "Why does the garage door automation keep failing?"
- "Analyze recent errors in the logs"

### Web Panel

Access Mímir through the Home Assistant sidebar. The panel provides the same functionality as Telegram with a chat-based interface.

## Support

For issues and feature requests, visit the [GitHub repository](https://github.com/yourusername/mimir).
