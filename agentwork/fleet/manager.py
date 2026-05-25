"""Fleet manager - orchestrates multiple agents."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

from agentwork.core.result import TaskResult
from agentwork.fleet.router import TaskRouter
from agentwork.fleet.pool import AgentPool

logger = logging.getLogger(__name__)

# Default number of consecutive failures before marking an agent unhealthy.
DEFAULT_FAILURE_THRESHOLD = 3


class FleetManager:
    """Orchestrates multiple agents, dispatches tasks, and collects results.

    Automatically marks agents as unhealthy after consecutive failures
    (configurable via failure_threshold). Agents can be manually restored
    via mark_healthy().

    Usage:
        fleet = FleetManager()
        fleet.register(office_agent)
        fleet.register(marketing_agent)
        result = fleet.dispatch("process_document", {"file": "report.pdf"})
    """

    def __init__(self, failure_threshold: int = DEFAULT_FAILURE_THRESHOLD) -> None:
        self.pool = AgentPool()
        self.router = TaskRouter(self.pool)
        self._results: List[Dict[str, Any]] = []
        self._failure_threshold = failure_threshold
        self._consecutive_failures: Dict[str, int] = defaultdict(int)

    def register(self, agent: Any) -> None:
        """Register an agent with the fleet."""
        self.pool.add(agent)
        self._consecutive_failures[agent.name] = 0
        logger.info("Registered agent '%s' with fleet", agent.name)

    def unregister(self, agent_name: str) -> None:
        """Remove an agent from the fleet."""
        self.pool.remove(agent_name)
        self._consecutive_failures.pop(agent_name, None)

    def _record_result(self, agent_name: str, result: TaskResult) -> None:
        """Track consecutive failures and auto-mark agents unhealthy."""
        if result.failed:
            self._consecutive_failures[agent_name] += 1
            if self._consecutive_failures[agent_name] >= self._failure_threshold:
                self.pool.mark_unhealthy(agent_name)
                logger.warning(
                    "Agent '%s' auto-marked unhealthy after %d consecutive failures",
                    agent_name,
                    self._consecutive_failures[agent_name],
                )
        else:
            self._consecutive_failures[agent_name] = 0

    def dispatch(
        self, task: str, input_data: Optional[Dict[str, Any]] = None
    ) -> TaskResult:
        """Dispatch a task to the best available agent.

        Uses the router to find the most suitable agent based on capabilities.
        Returns TaskResult.fail if no suitable agent is found.
        Automatically marks agents unhealthy after repeated failures.
        """
        agent = self.router.route(task)
        if agent is None:
            return TaskResult.fail(
                error=f"No agent available for task '{task}'",
                error_details={"available_agents": self.pool.list_names()},
            )

        result = agent.execute(task, input_data)
        self._record_result(agent.name, result)
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
        self._record_result(agent.name, result)
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
            self._record_result(agent.name, result)
            results.append(result)
        return results

    def mark_healthy(self, agent_name: str) -> None:
        """Manually mark an agent as healthy and reset its failure counter."""
        self.pool.mark_healthy(agent_name)
        self._consecutive_failures[agent_name] = 0

    @property
    def agents(self) -> List[Any]:
        """List all registered agents."""
        return self.pool.list_agents()

    @property
    def results_history(self) -> List[Dict[str, Any]]:
        """Access dispatch history."""
        return list(self._results)
