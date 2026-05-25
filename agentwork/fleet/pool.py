"""Agent pool - manages agent instances with health tracking."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentPool:
    """Pool of agent instances with health tracking.

    Manages registration, removal, and health status of agents.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, Any] = {}
        self._health: Dict[str, bool] = {}

    def add(self, agent: Any) -> None:
        """Add an agent to the pool."""
        name = agent.name
        self._agents[name] = agent
        self._health[name] = True
        logger.debug("Added agent '%s' to pool", name)

    def remove(self, name: str) -> Optional[Any]:
        """Remove an agent from the pool."""
        self._health.pop(name, None)
        return self._agents.pop(name, None)

    def get(self, name: str) -> Optional[Any]:
        """Get an agent by name."""
        return self._agents.get(name)

    def get_healthy(self) -> List[Any]:
        """Get all healthy agents."""
        return [
            agent
            for name, agent in self._agents.items()
            if self._health.get(name, False)
        ]

    def mark_unhealthy(self, name: str) -> None:
        """Mark an agent as unhealthy."""
        if name in self._health:
            self._health[name] = False
            logger.warning("Agent '%s' marked as unhealthy", name)

    def mark_healthy(self, name: str) -> None:
        """Mark an agent as healthy."""
        if name in self._health:
            self._health[name] = True
            logger.info("Agent '%s' marked as healthy", name)

    def is_healthy(self, name: str) -> bool:
        """Check if an agent is healthy."""
        return self._health.get(name, False)

    def list_agents(self) -> List[Any]:
        """List all agents in the pool."""
        return list(self._agents.values())

    def list_names(self) -> List[str]:
        """List all agent names."""
        return list(self._agents.keys())

    def size(self) -> int:
        """Get the pool size."""
        return len(self._agents)

    def __len__(self) -> int:
        return len(self._agents)
