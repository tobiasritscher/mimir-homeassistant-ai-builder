"""Tool registry for Mímir."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..llm.types import Tool as LLMTool
from ..utils.logging import get_logger

if TYPE_CHECKING:
    from .base import BaseTool

logger = get_logger(__name__)


class ToolNotFoundError(Exception):
    """Raised when a tool is not found in the registry."""

    pass


class ToolRegistry:
    """Registry for managing available tools.

    The registry maintains a collection of tools that can be invoked
    by the LLM. Tools are registered by name and can be looked up
    for execution.
    """

    def __init__(self) -> None:
        """Initialize an empty tool registry."""
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool.

        Args:
            tool: The tool to register.
        """
        if tool.name in self._tools:
            logger.warning("Overwriting existing tool: %s", tool.name)

        self._tools[tool.name] = tool
        logger.debug("Registered tool: %s", tool.name)

    def unregister(self, name: str) -> None:
        """Unregister a tool by name.

        Args:
            name: Name of the tool to unregister.
        """
        if name in self._tools:
            del self._tools[name]
            logger.debug("Unregistered tool: %s", name)

    def get(self, name: str) -> BaseTool:
        """Get a tool by name.

        Args:
            name: Name of the tool.

        Returns:
            The tool instance.

        Raises:
            ToolNotFoundError: If the tool is not registered.
        """
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool not found: {name}")
        return self._tools[name]

    def has(self, name: str) -> bool:
        """Check if a tool is registered.

        Args:
            name: Name of the tool.

        Returns:
            True if the tool is registered.
        """
        return name in self._tools

    @property
    def tools(self) -> list[BaseTool]:
        """Get all registered tools."""
        return list(self._tools.values())

    @property
    def tool_names(self) -> list[str]:
        """Get names of all registered tools."""
        return list(self._tools.keys())

    def get_llm_tools(self) -> list[LLMTool]:
        """Get all tools in LLM-compatible format.

        Returns:
            List of Tool objects for passing to the LLM.
        """
        return [tool.to_llm_tool() for tool in self._tools.values()]

    async def execute(self, name: str, **kwargs: object) -> str:
        """Execute a tool by name.

        Args:
            name: Name of the tool.
            **kwargs: Tool parameters.

        Returns:
            Tool execution result.

        Raises:
            ToolNotFoundError: If the tool is not registered.
        """
        tool = self.get(name)
        logger.info("Executing tool: %s", name)

        try:
            result = await tool.validate_and_execute(**kwargs)
            logger.debug("Tool %s returned: %s...", name, result[:100] if result else "")
            return result
        except Exception as e:
            logger.exception("Tool %s failed: %s", name, e)
            return f"Error executing {name}: {e}"

    def __len__(self) -> int:
        """Return the number of registered tools."""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools
