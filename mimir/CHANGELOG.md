# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
