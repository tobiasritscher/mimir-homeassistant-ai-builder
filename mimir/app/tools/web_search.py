"""Web search tool for Mímir.

Provides web search capabilities for researching Home Assistant
documentation, forums, HACS components, and other resources.
"""

from __future__ import annotations

from typing import Any

from duckduckgo_search import DDGS

from ..utils.logging import get_logger
from .base import BaseTool

logger = get_logger(__name__)


class WebSearchTool(BaseTool):
    """Web search tool using DuckDuckGo.

    Searches the web for Home Assistant related information,
    prioritizing official documentation and community resources.
    """

    # Sites to prioritize in search results
    PRIORITY_SITES = [
        "home-assistant.io",
        "community.home-assistant.io",
        "github.com/home-assistant",
        "hacs.xyz",
        "esphome.io",
    ]

    def __init__(self, max_results: int = 5) -> None:
        """Initialize the web search tool.

        Args:
            max_results: Maximum number of results to return.
        """
        self._max_results = max_results
        self._ddgs = DDGS()

    @property
    def name(self) -> str:
        """Return the tool name."""
        return "web_search"

    @property
    def description(self) -> str:
        """Return the tool description."""
        return (
            "Search the web for Home Assistant documentation, community discussions, "
            "HACS components, and troubleshooting information. Use this when you need "
            "to find solutions, best practices, or learn about specific integrations."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        """Return the parameter schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The search query. Be specific and include 'Home Assistant' "
                        "if searching for HA-related topics."
                    ),
                },
                "site": {
                    "type": "string",
                    "description": (
                        "Optional: Limit search to a specific site. "
                        "Options: 'docs' (home-assistant.io), 'forum' (community.home-assistant.io), "
                        "'hacs' (hacs.xyz), 'github' (github.com)"
                    ),
                    "enum": ["docs", "forum", "hacs", "github", None],
                },
            },
            "required": ["query"],
        }

    def _get_site_filter(self, site: str | None) -> str:
        """Get the site filter for the search query."""
        site_map = {
            "docs": "site:home-assistant.io",
            "forum": "site:community.home-assistant.io",
            "hacs": "site:hacs.xyz OR site:github.com/hacs",
            "github": "site:github.com",
        }
        return site_map.get(site or "", "")

    async def execute(self, query: str, site: str | None = None) -> str:
        """Execute a web search.

        Args:
            query: The search query.
            site: Optional site filter.

        Returns:
            Formatted search results.
        """
        try:
            # Build the search query
            search_query = query
            site_filter = self._get_site_filter(site)
            if site_filter:
                search_query = f"{site_filter} {query}"

            logger.info("Searching: %s", search_query)

            # Perform the search
            results = list(self._ddgs.text(search_query, max_results=self._max_results))

            if not results:
                return f"No results found for: {query}"

            # Format results
            formatted = [f"Search results for: {query}\n"]

            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                url = result.get("href", result.get("link", ""))
                snippet = result.get("body", result.get("snippet", ""))

                # Truncate long snippets
                if len(snippet) > 300:
                    snippet = snippet[:297] + "..."

                formatted.append(f"\n{i}. **{title}**")
                formatted.append(f"   URL: {url}")
                formatted.append(f"   {snippet}")

            return "\n".join(formatted)

        except Exception as e:
            logger.exception("Web search failed: %s", e)
            return f"Search failed: {e}"


class HomeAssistantDocsSearchTool(BaseTool):
    """Specialized tool for searching Home Assistant documentation."""

    def __init__(self) -> None:
        """Initialize the documentation search tool."""
        self._ddgs = DDGS()

    @property
    def name(self) -> str:
        """Return the tool name."""
        return "search_ha_docs"

    @property
    def description(self) -> str:
        """Return the tool description."""
        return (
            "Search the official Home Assistant documentation. Use this to find "
            "information about integrations, YAML configuration, automations, "
            "and other Home Assistant features."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        """Return the parameter schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for in the documentation.",
                },
            },
            "required": ["query"],
        }

    async def execute(self, query: str) -> str:
        """Search Home Assistant documentation."""
        try:
            search_query = f"site:home-assistant.io {query}"
            results = list(self._ddgs.text(search_query, max_results=5))

            if not results:
                return f"No documentation found for: {query}"

            formatted = ["Home Assistant Documentation Results:\n"]

            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                url = result.get("href", result.get("link", ""))
                snippet = result.get("body", result.get("snippet", ""))

                if len(snippet) > 200:
                    snippet = snippet[:197] + "..."

                formatted.append(f"\n{i}. {title}")
                formatted.append(f"   {url}")
                formatted.append(f"   {snippet}")

            return "\n".join(formatted)

        except Exception as e:
            logger.exception("Documentation search failed: %s", e)
            return f"Search failed: {e}"


class HACSSearchTool(BaseTool):
    """Tool for searching HACS components and custom integrations."""

    def __init__(self) -> None:
        """Initialize the HACS search tool."""
        self._ddgs = DDGS()

    @property
    def name(self) -> str:
        """Return the tool name."""
        return "search_hacs"

    @property
    def description(self) -> str:
        """Return the tool description."""
        return (
            "Search for HACS (Home Assistant Community Store) components, "
            "custom integrations, and Lovelace cards. Use this to find "
            "community-developed extensions for Home Assistant."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        """Return the parameter schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What kind of component or card to search for.",
                },
                "component_type": {
                    "type": "string",
                    "description": "Type of component to search for.",
                    "enum": ["integration", "plugin", "theme", "any"],
                },
            },
            "required": ["query"],
        }

    async def execute(self, query: str, component_type: str = "any") -> str:
        """Search for HACS components."""
        try:
            # Build search query
            type_terms = {
                "integration": "custom integration",
                "plugin": "lovelace card",
                "theme": "theme",
                "any": "",
            }
            type_term = type_terms.get(component_type, "")

            search_query = f"site:github.com HACS {type_term} {query} Home Assistant"
            results = list(self._ddgs.text(search_query, max_results=5))

            if not results:
                return f"No HACS components found for: {query}"

            formatted = [f"HACS Component Search Results for: {query}\n"]

            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                url = result.get("href", result.get("link", ""))
                snippet = result.get("body", result.get("snippet", ""))

                if len(snippet) > 200:
                    snippet = snippet[:197] + "..."

                formatted.append(f"\n{i}. {title}")
                formatted.append(f"   {url}")
                formatted.append(f"   {snippet}")

            formatted.append(
                "\nNote: To install HACS components, the user must add them manually "
                "through the HACS interface in Home Assistant."
            )

            return "\n".join(formatted)

        except Exception as e:
            logger.exception("HACS search failed: %s", e)
            return f"Search failed: {e}"
