# Contributing to Mímir

Thank you for your interest in contributing to Mímir! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Home Assistant instance for testing
- Anthropic API key (for LLM functionality)

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/tobiasritscher/mimir-homeassistant-ai-builder.git
   cd mimir-homeassistant-ai-builder
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Run linting and type checks:
   ```bash
   ruff check .
   mypy mimir/app
   ```

## Project Structure

```
mimir/
├── app/                    # Main application code
│   ├── conversation/       # Conversation management
│   ├── db/                 # Database (SQLite) operations
│   ├── git/                # Git version control
│   ├── ha/                 # Home Assistant API integration
│   ├── llm/                # LLM provider abstraction
│   ├── telegram/           # Telegram bot handler
│   ├── tools/              # Agent tools (HA operations, web search)
│   ├── web/                # Web UI handlers and templates
│   └── utils/              # Logging and utilities
├── config.yaml             # Add-on configuration schema
├── Dockerfile              # Container build
└── DOCS.md                 # User documentation
```

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Use the bug report template
3. Include:
   - Mímir version
   - Home Assistant version
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs

### Suggesting Features

1. Check the [Requirements.md](Requirements.md) for planned features
2. Open an issue with the feature request template
3. Describe the use case and expected behavior

### Submitting Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes following the code style guidelines
4. Run linting: `ruff check . && mypy mimir/app`
5. Commit with clear messages
6. Push and open a Pull Request

## Code Style

### Python

- Follow PEP 8
- Use type hints for all function signatures
- Docstrings for public functions and classes
- Keep functions focused and small
- Use `from __future__ import annotations` in all modules

### Linting

We use:
- **ruff**: For linting and formatting
- **mypy**: For type checking

Run before committing:
```bash
ruff check .
ruff format .
mypy mimir/app
```

### Commit Messages

- Use imperative mood: "Add feature" not "Added feature"
- Keep first line under 72 characters
- Reference issues: "Fix #123: Handle edge case"

## Adding New Tools

Tools are the primary way Mímir interacts with Home Assistant. To add a new tool:

1. Create a class inheriting from `BaseTool` in `mimir/app/tools/`
2. Define `name`, `description`, and `parameters`
3. Implement the `execute()` method
4. Register the tool in `MimirAgent._register_tools()`

Example:
```python
from .base import BaseTool

class MyNewTool(BaseTool):
    name = "my_tool"
    description = "Does something useful"
    parameters = {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "First parameter"}
        },
        "required": ["param1"]
    }

    async def execute(self, param1: str) -> str:
        # Implementation
        return f"Result for {param1}"
```

## Adding LLM Providers

To add support for a new LLM provider:

1. Create a class inheriting from `LLMProvider` in `mimir/app/llm/`
2. Implement the `complete()` method
3. Add provider to the factory in `mimir/app/llm/factory.py`
4. Update configuration schema in `mimir/config.yaml`

## Testing

Currently, Mímir does not have a comprehensive test suite. Contributions to add tests are welcome!

When testing manually:
1. Use a test Home Assistant instance
2. Test both Telegram and web interfaces
3. Verify tool execution produces expected results
4. Check audit logs at `/audit` endpoint

## Documentation

- Update DOCS.md for user-facing changes
- Update README.md for major features
- Add inline comments for complex logic
- Update CHANGELOG.md following Keep a Changelog format

## Questions?

Open an issue or reach out via GitHub Discussions.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
