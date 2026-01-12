# Mímir — Home Assistant Agent

## Requirements Specification v1.0

---

## 1. Project Overview

**Name:** Mímir (named after the Norse god of wisdom, inspired by the God of War characterisation)

**Purpose:** An intelligent agent that interfaces with Home Assistant to manage automations, scripts, helpers, scenes, dashboards, and perform log analysis. Mímir communicates with the user via Telegram and an in-Home-Assistant custom panel, providing technical guidance, executing changes, and maintaining version control of all modifications.

**License:** MIT

**Open Source:** Yes. The architecture must be model-agnostic and reasonably configurable for community adoption.

---

## 2. System Context

### 2.1 Existing Infrastructure

| Component         | Details                                                     |
| ----------------- | ----------------------------------------------------------- |
| Home Assistant    | OS installation running in VirtualBox on macOS              |
| External Access   | Nabu Casa                                                   |
| Server Name       | Asgard                                                      |
| Related Services  | Heimdall, Odin, Hildr (existing Norse-themed services)      |
| Container Runtime | Docker (available on host)                                  |
| HACS              | Installed (agent has no direct access, recommendation only) |

### 2.2 LLM Backend

Mímir must be model-agnostic, supporting the following providers through a unified interface:

- Anthropic (Claude, including Opus 4.5)
- OpenAI
- Google Gemini
- Azure AI Foundry
- Ollama (local models)
- vLLM (local models)

The user will select and configure their preferred provider. v1 will be developed against Claude (Opus 4.5) but the abstraction layer must be in place from the start.

---

## 3. Communication Interfaces

### 3.1 Telegram Bot

- **Integration:** Uses the official Home Assistant Telegram Bot integration (`telegram_bot`)
- **Reference:** https://www.home-assistant.io/integrations/telegram_bot
- **Access:** Single user only (owner)
- **Mode:** Reactive (responds to messages) with proactive notifications for detected issues
- **Proactive behaviour:** Notify only; never auto-fix without explicit instruction
- **Implementation note:** Mímir will register as a service consumer of the HA Telegram integration rather than running its own bot connection. This avoids duplicate bot instances and leverages existing HA infrastructure.

### 3.2 Home Assistant Custom Panel

- **Type:** Custom panel add-on (similar to other HA add-ons with embedded UI)
- **Design:** Pragmatic, functional, not fancy. Clean chat interface.
- **Framework:** Simple React or Vue-based panel (developer's choice for ease of implementation)

Both interfaces should provide equivalent functionality. The user should be able to start a conversation on Telegram and continue in the panel, or vice versa, with shared context.

---

## 4. Capabilities

### 4.1 Full Access (Create, Read, Update, Delete)

| Entity Type         | Permissions                                                                                                                                                              |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Automations         | Full CRUD, enable/disable                                                                                                                                                |
| Scripts             | Full CRUD                                                                                                                                                                |
| Scenes              | Full CRUD                                                                                                                                                                |
| Helpers             | Full CRUD (input_boolean, input_number, input_text, input_select, input_datetime, timer, counter)                                                                        |
| Dashboards/Lovelace | Read, modify cards, add entities to cards. Full view creation if requested. **Note: Marked as Beta for v1 due to LLM spatial reasoning limitations (see Section 19.2).** |
| Entities            | Rename, assign areas, assign labels                                                                                                                                      |

### 4.2 Read & Recommend Only

| Entity Type     | Permissions                                                       |
| --------------- | ----------------------------------------------------------------- |
| Add-ons         | Can recommend installation/configuration; user installs manually  |
| Integrations    | Can recommend; user configures manually                           |
| HACS components | Can recommend custom components and cards; user installs manually |

### 4.3 Explicitly Off-Limits

| Area                       | Reason   |
| -------------------------- | -------- |
| Network configuration      | Security |
| User management            | Security |
| SSL/certificate management | Security |

### 4.4 Log Analysis

- Analyse Home Assistant native logs on demand (not continuous monitoring)
- Identify errors, explain root causes, suggest fixes
- Recognise errors that can be safely ignored and advise accordingly
- Example error types: unavailable entities, integration errors, automation failures, deprecated YAML, resource warnings

### 4.5 Web Research

Mímir has internet access to research solutions and best practices.

**Use cases:**

- Searching for HACS components that solve a specific problem
- Looking up Home Assistant documentation for integrations or YAML syntax
- Finding community forum discussions about specific errors or configurations
- Researching best practices for automation patterns
- Investigating unknown entities, devices, or integration behaviours

**Sources to prioritise:**

- Home Assistant official documentation (https://www.home-assistant.io)
- Home Assistant Community Forums (https://community.home-assistant.io)
- HACS default repository and documentation
- GitHub repositories for specific integrations
- ESPHome documentation (if relevant)

**Implementation:** Web search tool available to the LLM, similar to function calling for other capabilities. The agent can search, retrieve, and synthesise information from these sources when needed.

---

## 5. Version Control

### 5.1 Git Integration

The following table summarises the Git configuration:

| Setting        | Value                                                          |
| -------------- | -------------------------------------------------------------- |
| Type           | Local Git repository                                           |
| Working Branch | `mimir-changes` (dedicated branch for all Mímir operations)    |
| Primary Branch | `main` or `master` (user's existing branch, used for rollback) |

### 5.2 Tracked Files

All configuration files are tracked, including:

- `configuration.yaml`
- `automations.yaml` (or automations directory)
- `scripts.yaml`
- `scenes.yaml`
- Helpers configuration
- Lovelace/dashboard configuration

**Excluded from tracking:** `secrets.yaml` must be added to `.gitignore`. Mímir may read secrets into memory for context but never commits this file.

### 5.3 Branch Strategy

On initialisation, Mímir creates a dedicated `mimir-changes` branch if it does not exist. All commits are made to this branch.

This provides a safety net: if Mímir breaks the system, the user can restore by running `git checkout main`. The primary branch remains untouched until the user explicitly merges.

The user can trigger a merge via command: "merge your changes to main" or similar.

### 5.4 Commit Behaviour

Commits occur automatically after each modification. Mímir generates meaningful, descriptive commit messages.

Example: "Modified kitchen motion automation: increased delay from 2 to 5 minutes"

### 5.5 Implementation Note

There may be an existing Home Assistant add-on for Git-based configuration backup. Evaluate existing solutions before building custom. If a suitable add-on exists, Mímir should integrate with it rather than duplicate functionality.

---

## 6. Action Approval System

### 6.1 Operating Modes

Mímir operates in one of three modes at any time:

| Mode            | Description                                                                       | Use Case                                                        |
| --------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **Chat Mode**   | Read-only. Mímir can analyse, explain, and recommend but cannot make any changes. | Safe exploration, learning, when user wants advice without risk |
| **Normal Mode** | Default. Some actions auto-approved, others require confirmation (see below).     | Day-to-day operation                                            |
| **YOLO Mode**   | All actions auto-approved for a limited duration.                                 | Intensive editing sessions                                      |

Mode can be changed via command: "enable Chat Mode", "switch to Normal Mode", "enable YOLO Mode".

### 6.2 Auto-Approved Actions (Normal Mode)

- Enabling or disabling automations/scripts
- Renaming entities
- Analysing logs (read-only)
- Reading and explaining configuration
- Minor edits to existing automations (e.g., changing delay values, thresholds)

### 6.3 Confirmation Required (Normal Mode)

- Creating new automations, scripts, or scenes
- Deleting any entity
- Modifying dashboard layouts
- Bulk operations (affecting more than 3 items)
- Changes to `configuration.yaml` or other core files

### 6.4 Chat Mode Behaviour

In Chat Mode, Mímir:

- Can read all configuration, logs, and state
- Can analyse and explain errors
- Can draft proposed changes and show them to the user
- Cannot execute any modifications
- Will remind the user to switch modes if they request a change: "I'm in Chat Mode, so I can't make that change. Here's what I would do—switch to Normal Mode if you'd like me to execute it."

### 6.5 YOLO Mode

A toggleable trust mode that auto-approves all actions for a defined period (e.g., 10 minutes). Intended for intensive editing sessions.

- Activated by user command: "enable YOLO mode" or similar
- Automatic expiry after configured duration
- User can deactivate early: "disable YOLO mode"
- Agent should remind user when YOLO mode is active and when it expires
- On failure during YOLO mode, auto-rollback is acceptable

---

## 7. Rate Limiting

Implement rate limiting on destructive actions as a safety measure.

**Proposed limits (configurable):**

- Maximum 5 deletions per hour without explicit override
- Maximum 20 modifications per hour without explicit override

If limits are reached, agent informs user and requests override confirmation to continue.

---

## 8. Audit Log

Maintain a separate audit log of all changes made by Mímir, independent of Home Assistant's own logs.

**Log entry format should include:**

- Timestamp
- Action type (create, update, delete, enable, disable)
- Target entity/file
- Summary of change
- Commit hash (if applicable)
- Approval method (auto-approved, user-confirmed, YOLO mode)

**Storage:** Local file or SQLite database (whichever is simpler to implement).

---

## 9. Memory & Context

### 9.1 Capabilities

Mímir should maintain long-term memory across conversations, including:

- User preferences (e.g., "I prefer motion sensors to have a 2-minute timeout")
- Ongoing projects (e.g., "We are refactoring the lighting automations this week")
- Device notes (e.g., "The bedroom sensor is unreliable")
- Historical context about past decisions

### 9.2 Memory Management

- User can add memories: "Remember that the hallway motion sensor needs replacing"
- User can remove memories: "Forget what I said about the bedroom sensor"
- User can query memories: "What do you remember about the kitchen?"

### 9.3 Implementation

Use the simplest viable solution: likely a local JSON or SQLite store. Memory should be searchable and retrievable by the LLM via function calling or tool use.

---

## 10. Error Handling

### 10.1 Failed Changes

- If a change fails (invalid YAML, entity not found, API error), report the failure clearly and wait for instructions
- Do not auto-rollback unless in YOLO mode, where auto-rollback on failure is acceptable
- Provide actionable error explanation

### 10.2 Home Assistant Unreachable

- If Home Assistant is unreachable, inform the user via Telegram (if Telegram is still functional)
- Do not queue commands or retry silently
- Clearly state: "I cannot reach Home Assistant. It may be restarting or there may be a network issue."

---

## 11. Authentication & Security

### 11.1 Home Assistant Authentication

- Mímir operates as its own dedicated Home Assistant user
- User has administrator privileges
- Authentication via long-lived access token (generated for the Mímir user)

### 11.2 Telegram Authentication

- Bot responds only to the configured owner's Telegram user ID
- Reject or ignore messages from other users

### 11.3 Panel Authentication

- Inherits Home Assistant's authentication
- Only accessible to logged-in HA users (in v1, this means only the owner)

---

## 12. Personality & Communication Style

### 12.1 Core Traits

- **Wise and knowledgeable:** Mímir understands the system deeply
- **Direct and blunt:** Gets to the point, does not sugarcoat
- **Sarcastic and witty:** Dry humour, charismatic, but never at the expense of clarity
- **Empathetic when appropriate:** Understands frustration, offers solutions
- **Honest about quality:** If an automation is poorly constructed, Mímir will say so
- **Technical:** Assumes the user understands Home Assistant concepts

### 12.2 Example Responses

**Good automation:**
"Done. The motion automation now waits 5 minutes before turning off. Commit pushed."

**Bad automation:**
"I've looked at this automation and frankly, it's a mess. You have three triggers doing the same thing and a condition that will never evaluate true because the entity doesn't exist. Want me to rewrite it properly?"

**Error analysis:**
"That error in `tempovermqtt` is happening because the MQTT topic changed but the automation still references the old one. Either update the topic or, if you've deprecated that sensor, delete the automation. Your call."

**Proactive notification:**
"I've spotted 12 errors in the logs since this morning. Most are that flaky Zigbee sensor you mentioned. One looks like a broken automation in the garage. Want me to dig in?"

### 12.3 Nordic Flavour

Subtle mythological references are acceptable but not forced:

- "The automation has been forged." (occasional)
- "This script holds no wisdom—only chaos." (when criticising)
- Avoid overuse; functionality and clarity come first.

---

## 13. Technical Architecture

### 13.1 Runtime

**Primary option:** Home Assistant Add-on

- Preferred for user simplicity and ecosystem integration
- Runs within the HA Supervisor environment

**Fallback option:** Standalone Docker container

- If add-on architecture proves limiting
- User has Docker available on host

### 13.2 Language & Framework

The following technologies will be used:

| Component        | Choice                                              | Notes                                                                                            |
| ---------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Language         | Python 3.11+                                        | Standard in HA ecosystem                                                                         |
| Async Framework  | asyncio-based                                       | For concurrent Telegram, HA API, LLM operations                                                  |
| YAML Handling    | `ruamel.yaml`                                       | Preserves comments, formatting, structure. Standard string replacement is explicitly prohibited. |
| HA Communication | MCP Client (primary), REST/WebSocket API (fallback) | Via long-lived access token                                                                      |
| Telegram         | Event Bus listener for `telegram_bot` integration   | Not a standalone bot connection                                                                  |
| Database         | SQLite                                              | For memory, audit log, conversation context                                                      |
| LLM              | Direct API to providers                             | Abstraction layer for multi-provider support                                                     |

### 13.3 Key Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                            Mímir Core                               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌─────────────┐  ┌────────────────────────┐  │
│  │  Telegram        │  │  HA Panel   │  │   LLM Interface        │  │
│  │  (via HA         │  │  Interface  │  │   (Direct API:         │  │
│  │   integration)   │  │  (WebSocket)│  │   Anthropic, OpenAI,   │  │
│  │                  │  │             │  │   Gemini, Ollama, etc.)│  │
│  └────────┬─────────┘  └──────┬──────┘  └───────────┬────────────┘  │
│           │                   │                     │               │
│           └───────────────────┼─────────────────────┘               │
│                               │                                     │
│                               ▼                                     │
│               ┌───────────────────────┐                             │
│               │   Conversation        │                             │
│               │   Manager             │                             │
│               │   (Context, Memory,   │                             │
│               │    Mode Control)      │                             │
│               └───────────┬───────────┘                             │
│                           │                                         │
│    ┌──────────────────────┼──────────────────────┐                  │
│    ▼                      ▼                      ▼                  │
│ ┌──────────┐      ┌─────────────┐      ┌─────────────┐              │
│ │  MCP     │      │  Git Manager│      │  Audit Log  │              │
│ │  Client  │      │  (branch:   │      │             │              │
│ │          │      │   mimir-    │      │             │              │
│ │          │      │   changes)  │      │             │              │
│ └────┬─────┘      └─────────────┘      └─────────────┘              │
│      │                    │                    │                    │
│      │  ┌─────────────────┴────────────────────┘                    │
│      │  │                                                           │
│      │  │  ┌─────────────┐  ┌─────────────┐                         │
│      │  │  │  Web Search │  │  File Map   │                         │
│      │  │  │             │  │  Indexer    │                         │
│      │  │  └─────────────┘  └──────┬──────┘                         │
│      │  │                          │                                │
└──────┼──┼──────────────────────────┼────────────────────────────────┘
       │  │                          │
       ▼  ▼                          ▼
┌──────────────────────────────────────────┐
│         Home Assistant                   │
│  ┌─────────────┐  ┌───────────────────┐  │
│  │  MCP Server │  │  Telegram Bot     │  │
│  │  Integration│  │  Integration      │  │
│  └─────────────┘  └───────────────────┘  │
│                                          │
│  ┌─────────────────────────────────────┐ │
│  │  Entities, Services, Automations,  │ │
│  │  Config, Logs, Dashboards          │ │
│  └─────────────────────────────────────┘ │
│                                          │
│  ┌─────────────────────────────────────┐ │
│  │  Configuration Files               │ │
│  │  (parsed via ruamel.yaml)          │ │
│  └─────────────────────────────────────┘ │
└──────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Git Repository  │  SQLite (Memory,     │
│  (mimir-changes  │  Audit, Context)     │
│   branch)        │                      │
└──────────────────────────────────────────┘
```

### 13.4 Home Assistant Communication via MCP

The user has the Home Assistant MCP Server integration configured (https://www.home-assistant.io/integrations/mcp_server). This exposes Home Assistant's capabilities via the Model Context Protocol.

**Architecture decision:** Mímir should act as an MCP client and use the MCP Server as its primary interface to Home Assistant. This provides several advantages over direct REST/WebSocket calls:

- Standardised protocol aligned with emerging LLM tooling ecosystem
- HA already exposes entities, services, and automations via MCP
- Reduces custom integration code
- Future-proof as MCP adoption grows

**Fallback:** Direct REST/WebSocket API access remains available for capabilities not exposed via MCP, or if MCP proves limiting during development.

**Investigation required:** During Phase 1, evaluate whether the MCP Server integration exposes all required functionality (automation CRUD, helper management, dashboard editing, log access). Document any gaps that require direct API access.

### 13.5 LLM Provider Architecture

**Direct API access:** Mímir connects directly to LLM providers (Anthropic, OpenAI, etc.) rather than routing through Home Assistant's conversation integrations (Anthropic integration, OpenAI Conversation integration).

**Rationale:** The HA conversation integrations are designed for the Assist voice pipeline and expose conversation agents, not raw completion endpoints. Mímir requires:

- Full tool/function calling support
- Long context windows
- Structured output control
- Streaming responses

These capabilities require direct API access.

**LLM Abstraction Layer:**

```python
# Conceptual interface
class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, messages: list, tools: list) -> Response:
        pass

class AnthropicProvider(LLMProvider): ...
class OpenAIProvider(LLMProvider): ...
class GeminiProvider(LLMProvider): ...
class OllamaProvider(LLMProvider): ...
class VLLMProvider(LLMProvider): ...
class AzureProvider(LLMProvider): ...
```

The provider is selected via configuration. Tool definitions (function calling) must be translated appropriately for each provider's format.

---

## 14. Configuration

The add-on/container should be configurable via a YAML or JSON configuration file and/or environment variables.

**Required configuration options:**

```yaml
# LLM Configuration
llm:
  provider: anthropic # anthropic, openai, gemini, azure, ollama, vllm
  api_key: ${MIMIR_LLM_API_KEY} # or use secrets
  model: claude-opus-4-5-20250514
  base_url: null # For Ollama, vLLM, Azure

# Home Assistant
homeassistant:
  url: http://homeassistant.local:8123
  token: ${MIMIR_HA_TOKEN}

# Telegram
telegram:
  bot_token: ${MIMIR_TELEGRAM_TOKEN}
  owner_id: 123456789 # Telegram user ID

# Git
git:
  enabled: true
  repo_path: /config # Path to HA config
  author_name: Mímir
  author_email: mimir@asgard.local

# Safety
safety:
  deletions_per_hour: 5
  modifications_per_hour: 20
  yolo_mode_duration_minutes: 10

# Memory
memory:
  storage_path: /data/mimir_memory.db
```

---

## 15. Out of Scope for v1

The following are explicitly deferred to future versions:

| Feature                         | Notes                        |
| ------------------------------- | ---------------------------- |
| External logging integration    | Grafana, Loki, etc.          |
| Add-on/integration installation | Mímir can recommend only     |
| HACS direct access              | Mímir can recommend only     |
| Multi-user support              | Single owner only in v1      |
| Safe mode (auto read-only)      | Not needed per user feedback |
| Voice interaction               | Text only in v1              |
| Mobile app notifications        | Telegram covers this         |

---

## 16. Development Phases

### Phase 1: Foundation & Discovery

- Project scaffolding, CI/CD, linting, MIT license setup
- LLM abstraction layer with Anthropic as first implementation
- **MCP Client implementation and capability investigation**
  - Connect to HA's MCP Server integration
  - Document which operations are supported vs. require direct API
- Basic Telegram integration via HA's telegram_bot
- Web search tool integration for research capabilities

### Phase 2: Core Functionality

- **File Map indexer:** Parse `configuration.yaml` to build include structure map. Consult before every write operation.
- Automation CRUD operations (via MCP where possible, direct API as fallback)
- Script and scene management
- Helper management
- Entity operations (rename, area assignment)
- Operating mode system (Chat Mode, Normal Mode, YOLO Mode)
- Approval system (auto-approve vs. confirm)

### Phase 3: Git & Safety

- Git integration (auto-commit, meaningful messages)
- Audit logging
- Rate limiting
- YOLO mode timer and auto-expiry

### Phase 4: Intelligence

- Log analysis and error explanation
- Proactive notifications (via HA Telegram integration)
- Memory system
- Web research integration for troubleshooting and recommendations

### Phase 5: Dashboard & Panel

- Dashboard/Lovelace modifications
- Custom HA panel development
- Shared context between Telegram and panel

### Phase 6: Polish & Open Source

- Additional LLM providers (OpenAI, Gemini, Ollama, vLLM, Azure)
- Documentation
- Example configurations
- Community-friendly defaults
- Repository preparation (README, CONTRIBUTING, issue templates)

---

## 17. Success Criteria

Mímir v1 is complete when:

1. User can converse with Mímir via Telegram and receive technically accurate, actionable responses
2. User can request creation, modification, or deletion of automations/scripts/scenes/helpers and have Mímir execute the changes
3. All changes are automatically committed to a local Git repository with meaningful messages
4. User can request log analysis and receive clear explanations of errors with suggested fixes
5. The approval system correctly distinguishes auto-approve from confirmation-required actions
6. YOLO mode functions as specified
7. Rate limiting prevents runaway destructive actions
8. An audit log captures all Mímir actions
9. Memory persists across conversations and is user-editable
10. The custom HA panel provides equivalent functionality to Telegram
11. The project is documented and publishable as open source under MIT license

---

## 18. Open Questions (Resolved)

The following items have been discussed and resolved:

| Question                      | Resolution                                                                                                                                                                                           |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Secrets handling**          | Add `secrets.yaml` to `.gitignore`. Mímir may read secrets into memory for context if needed, but never commits the file. The open-source template excludes it by default.                           |
| **Backup integration**        | Git is for config rollback only, not system backup. Document clearly that users must maintain HA native backups independently. Git does not capture database state, network configs, or add-on data. |
| **Multi-file automations**    | Mímir must build a "File Map" index by parsing `configuration.yaml` before any edit. This map identifies include structures and must be consulted before every write operation. See Section 19.1.    |
| **Dashboard storage mode**    | For UI-managed dashboards (`.storage/`), prefer API-based modifications. Direct file editing of storage files is fragile. Dashboard editing is marked Beta for v1. See Section 19.2.                 |
| **Shared context**            | Use local SQLite database for conversation history. Telegram `chat_id` and Panel `session_id` map to the same User Context record, enabling seamless conversation continuity across interfaces.      |
| **MCP capability coverage**   | Investigate during Phase 1. Document gaps requiring direct API fallback.                                                                                                                             |
| **Telegram message handling** | Implement as Event Bus listener within Mímir core, not as separate HA automation.                                                                                                                    |

---

## 19. Technical Risks & Constraints

### 19.1 The YAML Fragmentation Problem

Home Assistant configuration is notoriously fragmented, and this represents the single largest technical risk for Mímir.

**The problem:** Users split configurations using `!include`, `!include_dir_merge_list`, `!include_dir_named`, packages, and UI-managed storage (`.storage/`). A naive approach of editing YAML files directly will fail in numerous edge cases.

**Specific risks:**

- An LLM given a raw file dump may hallucinate file structure or attempt to write into an included file incorrectly.
- String replacement will corrupt YAML comments and formatting.
- If a user manages automations via the UI, they are stored in `.storage/core.config_entries`, not `automations.yaml`. Editing the wrong location will have no effect or cause conflicts.
- Packages combine multiple domains in single files, breaking assumptions about file-to-entity mapping.

**Mitigations for v1:**

1. Use `ruamel.yaml` (or equivalent) for all YAML operations. This library preserves comments, formatting, and structure.
2. Prefer Home Assistant's REST/WebSocket API for entity operations where possible. The API handles file writing correctly for UI-managed entities.
3. Before any file edit, Mímir must build a "File Map" by parsing `configuration.yaml` to understand the include structure. This map must be consulted before every write operation.
4. For v1, Mímir should only directly edit files it can verify are not UI-managed. When uncertain, use the API.
5. Add a pre-flight check: before writing, verify the target file is the correct location for the entity being modified.

**Constraint:** If Mímir cannot determine the correct file location with confidence, it should refuse the edit and explain the ambiguity to the user.

### 19.2 Dashboard Editing Limitations

LLMs perform poorly at spatial reasoning without vision capabilities. Requests like "move the button to the right" or "put this card next to that one" will likely produce broken layouts when working with raw YAML.

**Constraint for v1:** Dashboard editing is marked as **Experimental/Beta**. Mímir should:

- Focus on creating new views rather than modifying complex existing layouts.
- Handle simple operations: adding entities to existing cards, creating new cards with standard templates.
- Refuse or warn on spatially-dependent requests ("move", "reorder", "put next to").
- Suggest the user make spatial changes via the UI and ask Mímir for content-focused modifications.

### 19.3 Telegram Event Handling

The Home Assistant `telegram_bot` integration fires events (`telegram_command`, `telegram_text`) rather than providing a direct message handler.

**Implementation approach:** Mímir requires a background listener subscribing to the Home Assistant Event Bus to catch these events. This introduces slight latency compared to a direct bot connection.

**Alternative considered:** Having Mímir operate as the sole bot handler (bypassing HA's integration) would reduce latency but creates duplicate bot connections and loses HA ecosystem benefits. The event-based approach is preferred despite the latency trade-off.

**Implementation note:** The listener should be part of Mímir's core runtime, not implemented as a separate HA automation. This keeps the architecture cohesive and reduces configuration complexity for users.

### 19.4 Git Is Not Backup

Git version control serves a different purpose than Home Assistant's native backup system.

**Git provides:** Configuration file rollback, change history, meaningful diffs, the ability to revert specific automations.

**Git does not provide:** Database state, Z-Wave/Zigbee network configuration, integration credentials, add-on data, full system restore capability.

**Constraint:** The documentation must clearly state that Git integration supplements but does not replace HA's native backup. Users should maintain regular HA backups independently.

### 19.5 Branch Strategy for Safety

**Recommendation:** When Mímir initialises, it should create and work on a dedicated branch (e.g., `mimir-changes`).

**Rationale:** If Mímir breaks the system, the user can restore by checking out `main` or `master`. This is safer than committing directly to the primary branch.

**Workflow:**

1. On initialisation, create `mimir-changes` branch if it doesn't exist.
2. All Mímir commits go to this branch.
3. Periodically (or on user command), merge `mimir-changes` into `main`.
4. If rollback needed: `git checkout main` restores pre-Mímir state.

---

## 20. Personality Safety Override

While Mímir's sardonic personality enhances the user experience, it must never interfere with critical situations.

**Directive:** Mímir drops the persona immediately and responds directly and helpfully if:

- A critical safety hazard is detected (e.g., "my smart lock is broken and I'm locked out", "the smoke detector automation isn't working").
- The user is clearly distressed or in an emergency.
- The situation involves physical safety, security, or time-critical access issues.

In these cases, Mímir responds with clear, direct instructions without sarcasm or mythological references. The personality resumes once the critical situation is resolved.

---

## Appendix A: Reference Commands

Example natural language commands Mímir should understand:

**Automations:**

- "Create an automation that turns off all lights at midnight"
- "Disable the kitchen motion automation"
- "Why does the garage door automation keep failing?"
- "Show me all automations related to lighting"

**Scripts:**

- "Create a script called 'movie mode' that dims the living room to 20% and turns on the TV"
- "Delete the old test script"

**Helpers:**

- "Create an input_boolean called 'guest_mode'"
- "What helpers do I have for the heating system?"

**Dashboard:**

- "Add the bedroom humidity sensor to the bedroom card"
- "Create a new view for the garage"

**Logs:**

- "Analyse recent errors"
- "What's causing that MQTT error?"
- "Are there any warnings I should know about?"

**Research:**

- "Find me a HACS component for managing Zigbee groups"
- "What's the best practice for structuring lighting automations?"
- "Search the forums for this error: [error message]"
- "Is there an integration for [device/service]?"

**Mode control:**

- "Enable Chat Mode"
- "Switch to Normal Mode"
- "Enable YOLO Mode"
- "What mode am I in?"

**Memory:**

- "Remember that I want all motion timeouts to be 3 minutes by default"
- "What do you know about the kitchen setup?"
- "Forget what I said about the garage sensor"

**Control:**

- "Enable YOLO mode"
- "Commit current changes"
- "What have you changed today?"

---

## Appendix B: Nordic Personality Reference

For LLM prompt engineering, the following traits define Mímir's character:

> Mímir is the wisest being in Norse mythology, keeper of the well of wisdom beneath Yggdrasil. Odin sacrificed his eye to drink from this well. In this interpretation (inspired by God of War 2018/Ragnarök), Mímir is:
>
> - **Sardonic and witty:** Quick with a dry remark, especially when pointing out foolishness
> - **Genuinely helpful:** Despite the sarcasm, he wants to help and takes pride in good solutions
> - **Blunt about quality:** Will not pretend bad work is acceptable
> - **Knowledgeable:** Speaks with authority, explains clearly
> - **Empathetic:** Understands frustration, meets the user where they are
> - **Direct:** No unnecessary pleasantries, no filler
>
> He is not mean-spirited. His criticism is constructive, even when harsh. He respects competence and honest effort.

---

_Document generated: January 2025_
_Version: 1.0_
_Status: Ready for implementation_
