"""Tool registry for registering, discovering, and looking up tools."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agentwork.tools.base import Tool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing tool instances.

    Provides registration, lookup by name or capability (tag), and listing.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool in the registry."""
        if tool.name in self._tools:
            logger.warning("Overwriting existing tool '%s' in registry", tool.name)
        self._tools[tool.name] = tool
        logger.debug("Registered tool '%s'", tool.name)

    def unregister(self, name: str) -> Optional[Tool]:
        """Remove a tool from the registry. Returns the removed tool or None."""
        return self._tools.pop(name, None)

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name. Returns None if not found."""
        return self._tools.get(name)

    def get_by_tag(self, tag: str) -> List[Tool]:
        """Get all tools with a specific tag."""
        return [t for t in self._tools.values() if tag in t.tags]

    def list_tools(self) -> List[Tool]:
        """List all registered tools."""
        return list(self._tools.values())

    def list_names(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def has(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def clear(self) -> None:
        """Remove all tools from the registry."""
        self._tools.clear()

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
