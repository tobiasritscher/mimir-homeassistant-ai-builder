"""Tests for the tool registry."""

from __future__ import annotations

import pytest

from mimir.app.tools.registry import ToolNotFoundError, ToolRegistry

from ..conftest import MockTool


class TestToolRegistry:
    """Tests for ToolRegistry class."""

    def test_register_tool(self) -> None:
        """Test registering a tool."""
        registry = ToolRegistry()
        tool = MockTool(name="test_tool")

        registry.register(tool)

        assert "test_tool" in registry
        assert len(registry) == 1

    def test_get_tool(self) -> None:
        """Test getting a registered tool."""
        registry = ToolRegistry()
        tool = MockTool(name="test_tool")
        registry.register(tool)

        retrieved = registry.get("test_tool")

        assert retrieved is tool

    def test_get_tool_not_found(self) -> None:
        """Test getting a non-existent tool."""
        registry = ToolRegistry()

        with pytest.raises(ToolNotFoundError):
            registry.get("nonexistent")

    def test_has_tool(self) -> None:
        """Test checking if a tool exists."""
        registry = ToolRegistry()
        tool = MockTool(name="test_tool")
        registry.register(tool)

        assert registry.has("test_tool") is True
        assert registry.has("nonexistent") is False

    def test_unregister_tool(self) -> None:
        """Test unregistering a tool."""
        registry = ToolRegistry()
        tool = MockTool(name="test_tool")
        registry.register(tool)

        registry.unregister("test_tool")

        assert "test_tool" not in registry
        assert len(registry) == 0

    def test_tool_names(self) -> None:
        """Test getting tool names."""
        registry = ToolRegistry()
        registry.register(MockTool(name="tool1"))
        registry.register(MockTool(name="tool2"))

        names = registry.tool_names

        assert "tool1" in names
        assert "tool2" in names
        assert len(names) == 2

    def test_get_llm_tools(self) -> None:
        """Test getting tools in LLM format."""
        registry = ToolRegistry()
        registry.register(MockTool(name="test_tool", description="A test tool"))

        llm_tools = registry.get_llm_tools()

        assert len(llm_tools) == 1
        assert llm_tools[0].name == "test_tool"
        assert llm_tools[0].description == "A test tool"

    @pytest.mark.asyncio
    async def test_execute_tool(self) -> None:
        """Test executing a tool."""
        registry = ToolRegistry()
        tool = MockTool(name="test_tool", result="Success!")
        registry.register(tool)

        result = await registry.execute("test_tool", query="test query")

        assert result == "Success!"
        assert len(tool.calls) == 1
        assert tool.calls[0]["query"] == "test query"

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self) -> None:
        """Test executing an unknown tool."""
        registry = ToolRegistry()

        with pytest.raises(ToolNotFoundError):
            await registry.execute("nonexistent", query="test")
