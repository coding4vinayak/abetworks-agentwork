"""Fleet manager - orchestrates multiple agents."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agentwork.core.result import TaskResult
from agentwork.fleet.router import TaskRouter
from agentwork.fleet.pool import AgentPool

logger = logging.getLogger(__name__)


class FleetManager:
    """Orchestrates multiple agents, dispatches tasks, and collects results.

    Usage:
        fleet = FleetManager()
        fleet.register(office_agent)
        fleet.register(marketing_agent)
        result = fleet.dispatch("process_document", {"file": "report.pdf"})
    """

    def __init__(self) -> None:
        self.pool = AgentPool()
        self.router = TaskRouter(self.pool)
        self._results: List[Dict[str, Any]] = []

    def register(self, agent: Any) -> None:
        """Register an agent with the fleet."""
        self.pool.add(agent)
        logger.info("Registered agent '%s' with fleet", agent.name)

    def unregister(self, agent_name: str) -> None:
        """Remove an agent from the fleet."""
        self.pool.remove(agent_name)

    def dispatch(
        self, task: str, input_data: Optional[Dict[str, Any]] = None
    ) -> TaskResult:
        """Dispatch a task to the best available agent.

        Uses the router to find the most suitable agent based on capabilities.
        Returns TaskResult.fail if no suitable agent is found.
        """
        agent = self.router.route(task)
        if agent is None:
            return TaskResult.fail(
                error=f"No agent available for task '{task}'",
                error_details={"available_agents": self.pool.list_names()},
            )

        result = agent.execute(task, input_data)
        self._results.append(
            {
                "task": task,
                "agent": agent.name,
                "status": result.status.value,
            }
        )
        return result

    async def dispatch_async(
        self, task: str, input_data: Optional[Dict[str, Any]] = None
    ) -> TaskResult:
        """Dispatch a task asynchronously."""
        agent = self.router.route(task)
        if agent is None:
            return TaskResult.fail(
                error=f"No agent available for task '{task}'",
                error_details={"available_agents": self.pool.list_names()},
            )

        result = await agent.execute_async(task, input_data)
        self._results.append(
            {
                "task": task,
                "agent": agent.name,
                "status": result.status.value,
            }
        )
        return result

    def broadcast(
        self, task: str, input_data: Optional[Dict[str, Any]] = None
    ) -> List[TaskResult]:
        """Send a task to all agents that can handle it."""
        agents = self.router.find_all(task)
        results = []
        for agent in agents:
            result = agent.execute(task, input_data)
            results.append(result)
        return results

    @property
    def agents(self) -> List[Any]:
        """List all registered agents."""
        return self.pool.list_agents()

    @property
    def results_history(self) -> List[Dict[str, Any]]:
        """Access dispatch history."""
        return list(self._results)
