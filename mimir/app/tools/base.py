"""Base class for Mímir tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..llm.types import Tool as LLMTool


class BaseTool(ABC):
    """Abstract base class for all Mímir tools.

    Tools are capabilities that the LLM can invoke to perform actions
    or retrieve information. Each tool defines its parameters via
    JSON Schema and implements an execute method.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the tool name.

        This is the identifier used by the LLM to invoke the tool.
        Should be lowercase with underscores.
        """
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of what the tool does.

        This helps the LLM understand when to use the tool.
        Should be clear and concise.
        """
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """Return the JSON Schema for tool parameters.

        Example:
            {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        """
        ...

    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        """Execute the tool with the given parameters.

        Args:
            **kwargs: Tool parameters as defined in the schema.

        Returns:
            A string result that will be passed back to the LLM.
            Should be informative and formatted for LLM consumption.
        """
        ...

    def to_llm_tool(self) -> LLMTool:
        """Convert to LLM tool format."""
        return LLMTool(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )

    async def validate_and_execute(self, **kwargs: Any) -> str:
        """Validate parameters and execute the tool.

        Override this method if you need custom validation logic.
        """
        # TODO: Add JSON Schema validation if needed
        return await self.execute(**kwargs)
