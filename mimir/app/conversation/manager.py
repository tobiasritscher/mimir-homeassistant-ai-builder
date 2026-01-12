"""Conversation manager for Mímir.

Orchestrates conversations between the user, LLM, and tools.
Handles message history, tool execution, and response generation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..llm.types import Message, ToolCall
from ..utils.logging import get_logger
from ..utils.mode_manager import ModeManager, OperatingMode

if TYPE_CHECKING:
    from ..db.repository import AuditRepository, MemoryRepository
    from ..ha.types import UserContext
    from ..llm.base import LLMProvider
    from ..tools.registry import ToolRegistry

logger = get_logger(__name__)

# Mímir's system prompt
SYSTEM_PROMPT = """You are Mímir, an intelligent agent for Home Assistant. You are named after the Norse god of wisdom, keeper of the well of wisdom beneath Yggdrasil.

## Language
**Always respond in the same language as the user's message.** If the user writes in German, respond in German. If they write in English, respond in English. Match their language exactly.

## Your Personality
- **Wise and knowledgeable:** You understand Home Assistant deeply
- **Direct and blunt:** Get to the point, don't sugarcoat
- **Sardonic and witty:** Dry humor, charismatic, but never at the expense of clarity
- **Empathetic when appropriate:** Understand frustration, offer solutions
- **Honest about quality:** If an automation is poorly constructed, say so
- **Technical:** Assume the user understands Home Assistant concepts

Subtle mythological references are acceptable but not forced. Functionality and clarity come first.

## Critical Safety Override
Drop the persona immediately and respond directly and helpfully if:
- A critical safety hazard is detected (broken smart locks, malfunctioning smoke detectors, etc.)
- The user is clearly distressed or in an emergency
- The situation involves physical safety, security, or time-critical access issues

## Your Capabilities
You can:
- Manage automations, scripts, scenes, and helpers (create, modify, delete, enable/disable)
- Analyze Home Assistant logs and explain errors
- Rename entities and assign areas/labels
- Search the web for documentation, forum discussions, and HACS components
- Provide technical guidance on Home Assistant configuration

You cannot:
- Modify network configuration
- Manage users
- Handle SSL/certificate management
- Install add-ons or integrations directly (you can only recommend)

## Automation Editing Guidelines
When modifying automations, scripts, or scenes:
1. **Preserve existing logic**: Only change what the user explicitly asks for. Never rewrite entire automations.
2. **Show changes first**: Always display a diff of proposed changes before applying them.
3. **Explain impact**: Briefly describe what the change will affect.
4. **Minimal edits**: Make surgical changes, not wholesale replacements.
5. **Ask for confirmation**: For significant changes, ask "Shall I apply these changes?"

Example approach:
User: "Make the motion light turn off after 10 minutes instead of 5"
You: "I'll update the delay in your motion automation. Here's what changes:
```diff
- delay: '00:05:00'
+ delay: '00:10:00'
```
Everything else stays the same. Shall I apply this?"

**Never** remove or modify logic the user didn't ask about, even if you think it could be "improved".

## Operating Mode
Your current operating mode affects what actions require confirmation:
- **Chat Mode:** Read-only. You can analyze and recommend but cannot make changes.
- **Normal Mode:** Some actions auto-approved, others require confirmation.
- **YOLO Mode:** All actions auto-approved (time-limited).

## Response Style
- Be concise but complete
- Use Markdown formatting for clarity
- When showing code or YAML, use code blocks
- For complex operations, explain what you're doing
- Acknowledge when you don't know something
- If an automation or script is badly designed, say so constructively

## Example Responses

**Good automation created:**
"Done. The motion automation now waits 5 minutes before turning off. Commit pushed."

**Finding a poorly constructed automation:**
"I've looked at this automation and frankly, it's a mess. You have three triggers doing the same thing and a condition that will never evaluate true because the entity doesn't exist. Want me to rewrite it properly?"

**Error analysis:**
"That error in tempovermqtt is happening because the MQTT topic changed but the automation still references the old one. Either update the topic or, if you've deprecated that sensor, delete the automation. Your call."
"""


class ConversationManager:
    """Manages conversations with the LLM.

    Handles:
    - Message history
    - Tool execution loop
    - Response generation
    - Context management
    """

    def __init__(
        self,
        llm: LLMProvider,
        tool_registry: ToolRegistry,
        operating_mode: OperatingMode,
        mode_manager: ModeManager | None = None,
        audit_repository: AuditRepository | None = None,
        memory_repository: MemoryRepository | None = None,
        max_history: int = 50,
        max_tool_iterations: int = 10,
    ) -> None:
        """Initialize the conversation manager.

        Args:
            llm: The LLM provider to use.
            tool_registry: Registry of available tools.
            operating_mode: Current operating mode (deprecated, use mode_manager).
            mode_manager: Mode manager for operating mode enforcement.
            audit_repository: Optional repository for audit logging.
            memory_repository: Optional repository for long-term memory.
            max_history: Maximum number of messages to keep in history.
            max_tool_iterations: Maximum tool call iterations per turn.
        """
        self._llm = llm
        self._tool_registry = tool_registry
        self._operating_mode = operating_mode
        self._mode_manager = mode_manager
        self._audit = audit_repository
        self._memory = memory_repository
        self._max_history = max_history
        self._max_tool_iterations = max_tool_iterations
        self._messages: list[Message] = []

        # Current message context for audit logging
        self._current_source: str = "unknown"
        self._current_user_id: str | None = None
        self._current_audit_log_id: int | None = None

        # Current user context (set per message)
        self._current_user: UserContext | None = None

        # Cached memory summary (refreshed periodically)
        self._memory_summary: str = ""

    def set_message_context(
        self,
        source: str,
        user_id: str | None = None,
    ) -> None:
        """Set the context for the current message (for audit logging).

        Args:
            source: Source of the message ('telegram', 'web').
            user_id: Optional user identifier.
        """
        self._current_source = source
        self._current_user_id = user_id

    @property
    def operating_mode(self) -> OperatingMode:
        """Get the current operating mode."""
        if self._mode_manager:
            return self._mode_manager.current_mode
        return self._operating_mode

    @operating_mode.setter
    def operating_mode(self, mode: OperatingMode) -> None:
        """Set the operating mode."""
        self._operating_mode = mode
        if self._mode_manager:
            self._mode_manager.set_mode(mode)
        logger.info("Operating mode changed to: %s", mode.value)

    @property
    def mode_manager(self) -> ModeManager | None:
        """Get the mode manager."""
        return self._mode_manager

    def _check_mode_command(self, message: str) -> str | None:
        """Check if message is a mode command and handle it.

        Args:
            message: User message to check.

        Returns:
            Response message if it was a mode command, None otherwise.
        """
        if not self._mode_manager:
            return None

        # Check for mode query
        if self._mode_manager.is_mode_query(message):
            return self._mode_manager.format_mode_response()

        # Check for mode switch command
        new_mode = self._mode_manager.parse_mode_command(message)
        if new_mode:
            return self._mode_manager.set_mode(new_mode)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self._messages.clear()
        logger.debug("Conversation history cleared")

    async def load_history_from_audit(self, limit: int = 20) -> int:
        """Load conversation history from the audit database.

        This restores context after a restart by loading recent messages
        from the audit log.

        Args:
            limit: Maximum number of messages to load.

        Returns:
            Number of messages loaded.
        """
        if not self._audit:
            logger.debug("No audit repository, skipping history load")
            return 0

        try:
            # Get recent user and assistant messages
            logs = await self._audit.get_recent_logs(limit=limit * 2)

            # Filter to user/assistant messages and reverse to chronological order
            messages_to_load = []
            for log in reversed(logs):
                if log.message_type == "user":
                    messages_to_load.append(Message.user(log.content))
                elif log.message_type == "assistant":
                    messages_to_load.append(Message.assistant(content=log.content))

            # Limit to most recent messages
            if len(messages_to_load) > limit:
                messages_to_load = messages_to_load[-limit:]

            self._messages = messages_to_load
            logger.info("Loaded %d messages from audit history", len(self._messages))
            return len(self._messages)

        except Exception as e:
            logger.warning("Failed to load history from audit: %s", e)
            return 0

    def _trim_history(self) -> None:
        """Trim history to max_history messages."""
        if len(self._messages) > self._max_history:
            # Keep the most recent messages
            self._messages = self._messages[-self._max_history :]
            logger.debug("History trimmed to %d messages", len(self._messages))

    async def refresh_memory_summary(self) -> None:
        """Refresh the cached memory summary from the database."""
        if not self._memory:
            return

        try:
            self._memory_summary = await self._memory.get_memory_summary()
            if self._memory_summary:
                logger.debug("Loaded memory summary (%d chars)", len(self._memory_summary))
        except Exception as e:
            logger.warning("Failed to load memory summary: %s", e)

    def _build_system_prompt(self) -> str:
        """Build the full system prompt including user context and memories.

        Returns:
            The complete system prompt with user context and stored memories.
        """
        prompt = SYSTEM_PROMPT

        # Add current operating mode status
        if self._mode_manager:
            mode = self._mode_manager.current_mode
            prompt += "\n\n## Current Operating Mode\n"
            prompt += f"You are currently in **{mode.value.upper()}** mode.\n"
            if mode == OperatingMode.CHAT:
                prompt += (
                    "- You can ONLY read and analyze. You CANNOT make any changes.\n"
                    "- If the user asks you to modify something, explain that you're in "
                    "Chat mode and they need to switch to Normal or YOLO mode.\n"
                    "- Say: 'I'm in Chat mode, so I can only analyze and recommend. "
                    "Switch to Normal mode if you want me to make changes.'"
                )
            elif mode == OperatingMode.YOLO:
                remaining = self._mode_manager.yolo_remaining_minutes
                prompt += (
                    f"- All actions are auto-approved. YOLO mode expires in {remaining:.1f} minutes.\n"
                    "- Execute changes directly without asking for confirmation.\n"
                    "- Be efficient but still explain what you're doing."
                )
            else:  # NORMAL
                prompt += (
                    "- Read operations are auto-approved.\n"
                    "- For create/update operations, briefly explain what you'll do before executing.\n"
                    "- For delete operations, ask for confirmation before executing."
                )

        # Add user context if available
        if self._current_user:
            prompt += "\n\n## Current User\n"
            prompt += f"You are talking to **{self._current_user.friendly_name}**"
            if self._current_user.username:
                prompt += f" (username: {self._current_user.username})"
            prompt += f"\nThey are accessing you via: {self._current_user.source}\n"
            prompt += (
                "Adapt your responses to this user's preferences if you remember any "
                "from the facts below."
            )

        # Add memory summary if available
        if self._memory_summary:
            prompt += f"\n\n{self._memory_summary}"

        return prompt

    async def _execute_tool_calls(
        self,
        tool_calls: list[ToolCall],
    ) -> list[Message]:
        """Execute tool calls and return result messages.

        Args:
            tool_calls: List of tool calls to execute.

        Returns:
            List of tool result messages.
        """
        results = []

        for tool_call in tool_calls:
            logger.info("Executing tool: %s", tool_call.name)

            try:
                if self._tool_registry.has(tool_call.name):
                    result = await self._tool_registry.execute(
                        tool_call.name,
                        **tool_call.arguments,
                    )
                else:
                    result = f"Error: Unknown tool '{tool_call.name}'"
                    logger.warning("Unknown tool requested: %s", tool_call.name)

                is_error = result.startswith("Error:")

            except Exception as e:
                logger.exception("Tool execution failed: %s", e)
                result = f"Error executing {tool_call.name}: {e}"
                is_error = True

            results.append(
                Message.tool_result(
                    tool_call_id=tool_call.id,
                    content=result,
                    is_error=is_error,
                )
            )

        return results

    async def process_message(
        self,
        user_message: str,
        user_context: UserContext | None = None,
    ) -> str:
        """Process a user message and generate a response.

        This method:
        1. Checks for mode commands first
        2. Adds the user message to history
        3. Sends to LLM with available tools
        4. Executes any tool calls
        5. Continues until LLM provides a final response

        Args:
            user_message: The user's message.
            user_context: Context about the current user (from HA headers or Telegram).

        Returns:
            The assistant's response text.
        """
        # Set user context for this message
        self._current_user = user_context
        if user_context:
            self._current_source = user_context.source
            self._current_user_id = user_context.user_id

        # Check for mode commands first (before adding to history)
        mode_response = self._check_mode_command(user_message)
        if mode_response:
            # Log the mode command and response
            if self._audit:
                try:
                    await self._audit.log_message(
                        source=self._current_source,
                        message_type="user",
                        content=user_message,
                        user_id=self._current_user_id,
                    )
                    await self._audit.log_message(
                        source=self._current_source,
                        message_type="assistant",
                        content=mode_response,
                        user_id=self._current_user_id,
                    )
                except Exception as e:
                    logger.warning("Failed to log mode command: %s", e)
            return mode_response

        # Add user message to history
        self._messages.append(Message.user(user_message))
        self._trim_history()

        logger.info("Processing message: %s...", user_message[:50])

        # Log user message to audit
        if self._audit:
            try:
                self._current_audit_log_id = await self._audit.log_message(
                    source=self._current_source,
                    message_type="user",
                    content=user_message,
                    user_id=self._current_user_id,
                )
            except Exception as e:
                logger.warning("Failed to log user message: %s", e)

        # Get available tools
        tools = self._tool_registry.get_llm_tools()

        # Refresh memory summary (includes any new memories from this session)
        await self.refresh_memory_summary()

        # Build system prompt with memories
        system_prompt = self._build_system_prompt()

        # Tool execution loop
        iterations = 0
        while iterations < self._max_tool_iterations:
            iterations += 1

            # Get LLM response
            response = await self._llm.complete(
                messages=self._messages,
                tools=tools if tools else None,
                system=system_prompt,
            )

            logger.debug(
                "LLM response: stop_reason=%s, has_tool_calls=%s",
                response.stop_reason,
                response.has_tool_calls,
            )

            # Handle tool calls
            if response.has_tool_calls and response.tool_calls:
                # Add assistant message with tool calls
                self._messages.append(
                    Message.assistant(
                        content=response.content,
                        tool_calls=response.tool_calls,
                    )
                )

                # Execute tools and add results
                tool_results = await self._execute_tool_calls(response.tool_calls)
                self._messages.extend(tool_results)

                # Continue loop to get next response
                continue

            # No tool calls - we have a final response
            if response.content:
                self._messages.append(Message.assistant(content=response.content))
                await self._log_assistant_response(response.content)
                return response.content

            # Edge case: no content and no tool calls
            logger.warning("LLM returned empty response")
            fallback = "I apologize, but I couldn't generate a response. Please try again."
            await self._log_assistant_response(fallback)
            return fallback

        # Exceeded max iterations
        logger.warning("Exceeded max tool iterations (%d)", self._max_tool_iterations)
        limit_response = (
            "I've been working on this for a while and hit a limit. "
            "Here's what I found so far - let me know if you need me to continue."
        )
        await self._log_assistant_response(limit_response)
        return limit_response

    async def _log_assistant_response(self, content: str) -> None:
        """Log an assistant response to the audit log.

        Args:
            content: The response content.
        """
        if not self._audit:
            return

        try:
            await self._audit.log_message(
                source=self._current_source,
                message_type="assistant",
                content=content,
                user_id=self._current_user_id,
            )
        except Exception as e:
            logger.warning("Failed to log assistant response: %s", e)

    def get_history(self) -> list[dict[str, Any]]:
        """Get conversation history in a serializable format.

        Returns:
            List of message dictionaries with 'role' and 'content'.
        """
        history = []
        for msg in self._messages:
            # Skip tool results - they're internal
            if msg.role.value == "user" or (msg.role.value == "assistant" and not msg.tool_calls):
                content = ""
                if isinstance(msg.content, str):
                    content = msg.content
                elif isinstance(msg.content, list):
                    # Extract text content from content blocks
                    for block in msg.content:
                        if hasattr(block, "text") and block.text:
                            content += block.text

                if content:
                    history.append(
                        {
                            "role": msg.role.value,
                            "content": content,
                        }
                    )

        return history

    async def get_context_summary(self) -> str:
        """Get a summary of the current conversation context.

        Returns:
            A text summary of the conversation state.
        """
        return (
            f"Conversation has {len(self._messages)} messages. "
            f"Operating mode: {self._operating_mode.value}. "
            f"Available tools: {', '.join(self._tool_registry.tool_names)}."
        )
