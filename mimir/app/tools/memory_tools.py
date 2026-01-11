"""Memory tools for Mímir.

These tools allow the LLM to store and recall long-term memories
about the user's preferences and home setup.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..utils.logging import get_logger
from .base import BaseTool

if TYPE_CHECKING:
    from ..db.repository import MemoryRepository

logger = get_logger(__name__)


class StoreMemoryTool(BaseTool):
    """Tool to store a new memory."""

    def __init__(self, memory_repo: MemoryRepository) -> None:
        self._memory_repo = memory_repo

    @property
    def name(self) -> str:
        return "store_memory"

    @property
    def description(self) -> str:
        return (
            "Store a fact or preference to remember long-term. Use this when the user says "
            "'merke dir', 'remember this', or shares important information about their home, "
            "devices, preferences, or routines that should be remembered across conversations. "
            "Be concise - store the essence, not the full conversation."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The fact or preference to remember. Be concise and specific.",
                },
                "category": {
                    "type": "string",
                    "enum": [
                        "user_preference",
                        "device_info",
                        "automation_note",
                        "home_layout",
                        "routine",
                        "general",
                    ],
                    "description": (
                        "Category: user_preference (language, style), device_info (device names, locations), "
                        "automation_note (notes about automations), home_layout (rooms, areas), "
                        "routine (schedules, habits), general (other facts)."
                    ),
                },
            },
            "required": ["content", "category"],
        }

    async def execute(self, **kwargs: Any) -> str:
        content = kwargs.get("content", "")
        category = kwargs.get("category", "general")

        if not content:
            return "Error: content is required."

        try:
            memory_id = await self._memory_repo.add_memory(
                content=content,
                category=category,
            )
            return f"Gespeichert (ID: {memory_id}): {content}"

        except Exception as e:
            logger.exception("Failed to store memory: %s", e)
            return f"Error storing memory: {e}"


class RecallMemoriesTool(BaseTool):
    """Tool to search and recall memories."""

    def __init__(self, memory_repo: MemoryRepository) -> None:
        self._memory_repo = memory_repo

    @property
    def name(self) -> str:
        return "recall_memories"

    @property
    def description(self) -> str:
        return (
            "Search stored memories for relevant information. Use this to recall previously "
            "stored facts about the user's home, preferences, or devices."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term to find relevant memories.",
                },
                "category": {
                    "type": "string",
                    "enum": [
                        "user_preference",
                        "device_info",
                        "automation_note",
                        "home_layout",
                        "routine",
                        "general",
                    ],
                    "description": "Optional: Filter by category.",
                },
            },
            "required": [],
        }

    async def execute(self, **kwargs: Any) -> str:
        query = kwargs.get("query", "")
        category = kwargs.get("category")

        try:
            if query:
                memories = await self._memory_repo.search_memories(query)
            elif category:
                memories = await self._memory_repo.get_memories_by_category(category)
            else:
                memories = await self._memory_repo.get_all_memories()

            if not memories:
                return "Keine Erinnerungen gefunden."

            results = []
            for mem in memories[:20]:  # Limit to 20 results
                results.append(f"- [{mem.category}] {mem.content}")

            return f"Gefundene Erinnerungen ({len(memories)}):\n" + "\n".join(results)

        except Exception as e:
            logger.exception("Failed to recall memories: %s", e)
            return f"Error recalling memories: {e}"


class ForgetMemoryTool(BaseTool):
    """Tool to delete a memory."""

    def __init__(self, memory_repo: MemoryRepository) -> None:
        self._memory_repo = memory_repo

    @property
    def name(self) -> str:
        return "forget_memory"

    @property
    def description(self) -> str:
        return (
            "Delete a stored memory by its ID. Use this when the user wants to remove "
            "outdated or incorrect information."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "integer",
                    "description": "The ID of the memory to delete.",
                },
            },
            "required": ["memory_id"],
        }

    async def execute(self, **kwargs: Any) -> str:
        memory_id = kwargs.get("memory_id")

        if memory_id is None:
            return "Error: memory_id is required."

        try:
            deleted = await self._memory_repo.delete_memory(memory_id)

            if deleted:
                return f"Erinnerung {memory_id} gelöscht."
            else:
                return f"Erinnerung {memory_id} nicht gefunden."

        except Exception as e:
            logger.exception("Failed to delete memory: %s", e)
            return f"Error deleting memory: {e}"
