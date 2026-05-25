"""Task router - routes tasks to best available agent based on capabilities."""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from agentwork.fleet.pool import AgentPool

logger = logging.getLogger(__name__)


class TaskRouter:
    """Routes tasks to the most suitable agent based on capabilities and tool availability.

    Routing strategy:
    1. Check if any agent has a tool matching the task name exactly.
    2. Check if any agent has capabilities matching the task.
    3. Fall back to the first available healthy agent.
    """

    def __init__(self, pool: Optional[AgentPool] = None) -> None:
        self.pool = pool if pool is not None else AgentPool()

    def route(self, task: str) -> Optional[Any]:
        """Find the best agent for a task. Returns None if no match found."""
        healthy_agents = self.pool.get_healthy()

        # First: exact tool match
        for agent in healthy_agents:
            if hasattr(agent, "tool_names") and task in agent.tool_names:
                logger.debug("Routed task '%s' to agent '%s' (tool match)", task, agent.name)
                return agent

        # Second: capability match
        for agent in healthy_agents:
            if hasattr(agent, "capabilities"):
                for cap in agent.capabilities:
                    if task.lower() in cap.lower() or cap.lower() in task.lower():
                        logger.debug(
                            "Routed task '%s' to agent '%s' (capability match)",
                            task,
                            agent.name,
                        )
                        return agent

        # No match found
        logger.warning("No agent found for task '%s'", task)
        return None

    def find_all(self, task: str) -> List[Any]:
        """Find all agents that can handle a task."""
        healthy_agents = self.pool.get_healthy()
        matching = []

        for agent in healthy_agents:
            if hasattr(agent, "tool_names") and task in agent.tool_names:
                matching.append(agent)
            elif hasattr(agent, "capabilities"):
                for cap in agent.capabilities:
                    if task.lower() in cap.lower() or cap.lower() in task.lower():
                        matching.append(agent)
                        break

        return matching
