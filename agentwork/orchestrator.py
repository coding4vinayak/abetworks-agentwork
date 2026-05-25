"""Company orchestrator for complex multi-agent task execution.

Breaks high-level tasks into sub-tasks, assigns them to the right
agent based on capabilities, handles dependencies (piping output
from one to next), runs independent tasks in parallel, and
tracks everything by task_id for remote polling.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from agentwork.core.agent import Agent
from agentwork.core.result import TaskResult
from agentwork.fleet.manager import FleetManager

logger = logging.getLogger(__name__)


class CompanyTaskResult(BaseModel):
    """Result from an orchestrated company task."""

    task_id: str
    status: str = "success"
    sub_results: List[Dict[str, Any]] = Field(default_factory=list)
    final_output: Any = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CompanyOrchestrator:
    """Orchestrates complex tasks across a fleet of specialized agents.

    Breaks high-level tasks into sub-tasks, assigns them to the right
    agent based on capabilities, handles dependencies (piping output
    from one to next), runs independent tasks in parallel, and
    tracks everything by task_id.
    """

    def __init__(
        self,
        agents: Optional[List[Agent]] = None,
        failure_threshold: int = 3,
    ) -> None:
        self._fleet = FleetManager(failure_threshold=failure_threshold)
        self._orchestrations: Dict[str, Dict[str, Any]] = {}

        if agents:
            for agent in agents:
                self._fleet.register(agent)

    def add_agent(self, agent: Agent) -> None:
        """Register an agent with the orchestrator."""
        self._fleet.register(agent)

    def remove_agent(self, agent_name: str) -> None:
        """Remove an agent from the orchestrator."""
        self._fleet.unregister(agent_name)

    @property
    def agents(self) -> List[Any]:
        """List all registered agents."""
        return self._fleet.agents

    def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an orchestration by task_id."""
        return self._orchestrations.get(task_id)

    def orchestrate(
        self,
        task_description: str,
        sub_tasks: List[Dict[str, Any]],
        input_data: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
    ) -> CompanyTaskResult:
        """Execute a complex task with explicit sub-task definitions.

        Args:
            task_description: Human-readable description of the overall goal.
            sub_tasks: List of dicts defining sub-tasks, each with:
                - name: str (the tool name to execute)
                - input_data: dict (input for this sub-task, or None to use piped output)
                - depends_on: List[str] (names of sub-tasks this depends on)
            input_data: Initial input data shared across independent sub-tasks.
            task_id: Client-specified ID for tracking (auto-generated if None).

        Returns:
            CompanyTaskResult with aggregated results.
        """
        task_id = task_id or str(uuid.uuid4())
        start = time.time()

        self._orchestrations[task_id] = {
            "task_id": task_id,
            "description": task_description,
            "status": "running",
            "sub_tasks": {st["name"]: "pending" for st in sub_tasks},
        }

        sub_results: List[Dict[str, Any]] = []
        outputs: Dict[str, Any] = {}

        # Build dependency graph
        dependency_map: Dict[str, List[str]] = {}
        task_map: Dict[str, Dict[str, Any]] = {}
        for st in sub_tasks:
            name = st["name"]
            dependency_map[name] = st.get("depends_on", []) or []
            task_map[name] = st

        # Topological execution: process tasks level by level
        completed: set = set()
        while len(completed) < len(sub_tasks):
            # Find tasks whose dependencies are all met
            ready = []
            for st in sub_tasks:
                name = st["name"]
                if name in completed:
                    continue
                deps = dependency_map[name]
                if all(d in completed for d in deps):
                    ready.append(st)

            if not ready:
                # No progress possible - circular dependency or missing dep
                for st in sub_tasks:
                    name = st["name"]
                    if name not in completed:
                        sub_results.append({
                            "agent_name": "unknown",
                            "sub_task": name,
                            "status": "failure",
                            "output": None,
                            "error": "Unresolvable dependency",
                        })
                        completed.add(name)
                break

            # Run ready tasks in parallel
            if len(ready) > 1:
                with ThreadPoolExecutor(max_workers=len(ready)) as executor:
                    futures = {}
                    for st in ready:
                        futures[st["name"]] = executor.submit(
                            self._execute_sub_task, st, input_data, outputs
                        )
                    for name, future in futures.items():
                        result = future.result()
                        sub_results.append(result)
                        outputs[name] = result.get("output")
                        completed.add(name)
                        self._orchestrations[task_id]["sub_tasks"][name] = result["status"]
            else:
                st = ready[0]
                result = self._execute_sub_task(st, input_data, outputs)
                sub_results.append(result)
                outputs[st["name"]] = result.get("output")
                completed.add(st["name"])
                self._orchestrations[task_id]["sub_tasks"][st["name"]] = result["status"]

        duration_ms = (time.time() - start) * 1000

        # Determine overall status
        statuses = [r["status"] for r in sub_results]
        if all(s == "success" for s in statuses):
            overall_status = "success"
        elif all(s == "failure" for s in statuses):
            overall_status = "failure"
        else:
            overall_status = "partial"

        # Final output is the last sub-result output
        final_output = sub_results[-1]["output"] if sub_results else None

        self._orchestrations[task_id]["status"] = overall_status

        return CompanyTaskResult(
            task_id=task_id,
            status=overall_status,
            sub_results=sub_results,
            final_output=final_output,
            duration_ms=duration_ms,
            metadata={"description": task_description},
        )

    async def orchestrate_async(
        self,
        task_description: str,
        sub_tasks: List[Dict[str, Any]],
        input_data: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
    ) -> CompanyTaskResult:
        """Async version of orchestrate."""
        task_id = task_id or str(uuid.uuid4())
        start = time.time()

        self._orchestrations[task_id] = {
            "task_id": task_id,
            "description": task_description,
            "status": "running",
            "sub_tasks": {st["name"]: "pending" for st in sub_tasks},
        }

        sub_results: List[Dict[str, Any]] = []
        outputs: Dict[str, Any] = {}

        # Build dependency graph
        dependency_map: Dict[str, List[str]] = {}
        task_map: Dict[str, Dict[str, Any]] = {}
        for st in sub_tasks:
            name = st["name"]
            dependency_map[name] = st.get("depends_on", []) or []
            task_map[name] = st

        # Topological execution: process tasks level by level
        completed: set = set()
        while len(completed) < len(sub_tasks):
            ready = []
            for st in sub_tasks:
                name = st["name"]
                if name in completed:
                    continue
                deps = dependency_map[name]
                if all(d in completed for d in deps):
                    ready.append(st)

            if not ready:
                for st in sub_tasks:
                    name = st["name"]
                    if name not in completed:
                        sub_results.append({
                            "agent_name": "unknown",
                            "sub_task": name,
                            "status": "failure",
                            "output": None,
                            "error": "Unresolvable dependency",
                        })
                        completed.add(name)
                break

            # Run ready tasks concurrently
            if len(ready) > 1:
                tasks = [
                    self._execute_sub_task_async(st, input_data, outputs)
                    for st in ready
                ]
                results = await asyncio.gather(*tasks)
                for st, result in zip(ready, results):
                    sub_results.append(result)
                    outputs[st["name"]] = result.get("output")
                    completed.add(st["name"])
                    self._orchestrations[task_id]["sub_tasks"][st["name"]] = result["status"]
            else:
                st = ready[0]
                result = await self._execute_sub_task_async(st, input_data, outputs)
                sub_results.append(result)
                outputs[st["name"]] = result.get("output")
                completed.add(st["name"])
                self._orchestrations[task_id]["sub_tasks"][st["name"]] = result["status"]

        duration_ms = (time.time() - start) * 1000

        statuses = [r["status"] for r in sub_results]
        if all(s == "success" for s in statuses):
            overall_status = "success"
        elif all(s == "failure" for s in statuses):
            overall_status = "failure"
        else:
            overall_status = "partial"

        final_output = sub_results[-1]["output"] if sub_results else None

        self._orchestrations[task_id]["status"] = overall_status

        return CompanyTaskResult(
            task_id=task_id,
            status=overall_status,
            sub_results=sub_results,
            final_output=final_output,
            duration_ms=duration_ms,
            metadata={"description": task_description},
        )

    def _execute_sub_task(
        self,
        sub_task: Dict[str, Any],
        shared_input: Optional[Dict[str, Any]],
        outputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a single sub-task using the fleet manager."""
        name = sub_task["name"]
        task_input = sub_task.get("input_data")
        depends_on = sub_task.get("depends_on", []) or []

        # If this task depends on others, pipe their outputs as input
        if depends_on and not task_input:
            if len(depends_on) == 1:
                dep_output = outputs.get(depends_on[0])
                if isinstance(dep_output, dict):
                    task_input = self._filter_input_for_tool(name, dep_output)
                else:
                    task_input = {"input": dep_output}
            else:
                combined = {}
                for dep in depends_on:
                    dep_out = outputs.get(dep)
                    if isinstance(dep_out, dict):
                        combined.update(dep_out)
                    else:
                        combined[dep] = dep_out
                task_input = self._filter_input_for_tool(name, combined)
        elif not task_input and shared_input:
            task_input = shared_input

        try:
            result = self._fleet.dispatch(name, task_input)
            agent_name = self._find_agent_for_task(name)
            return {
                "agent_name": agent_name or "unknown",
                "sub_task": name,
                "status": "success" if result.success else "failure",
                "output": result.output,
            }
        except Exception as e:
            logger.error("Sub-task '%s' failed: %s", name, str(e))
            return {
                "agent_name": "unknown",
                "sub_task": name,
                "status": "failure",
                "output": None,
                "error": str(e),
            }

    async def _execute_sub_task_async(
        self,
        sub_task: Dict[str, Any],
        shared_input: Optional[Dict[str, Any]],
        outputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a single sub-task asynchronously."""
        name = sub_task["name"]
        task_input = sub_task.get("input_data")
        depends_on = sub_task.get("depends_on", []) or []

        if depends_on and not task_input:
            if len(depends_on) == 1:
                dep_output = outputs.get(depends_on[0])
                if isinstance(dep_output, dict):
                    task_input = self._filter_input_for_tool(name, dep_output)
                else:
                    task_input = {"input": dep_output}
            else:
                combined = {}
                for dep in depends_on:
                    dep_out = outputs.get(dep)
                    if isinstance(dep_out, dict):
                        combined.update(dep_out)
                    else:
                        combined[dep] = dep_out
                task_input = self._filter_input_for_tool(name, combined)
        elif not task_input and shared_input:
            task_input = shared_input

        try:
            result = await self._fleet.dispatch_async(name, task_input)
            agent_name = self._find_agent_for_task(name)
            return {
                "agent_name": agent_name or "unknown",
                "sub_task": name,
                "status": "success" if result.success else "failure",
                "output": result.output,
            }
        except Exception as e:
            logger.error("Async sub-task '%s' failed: %s", name, str(e))
            return {
                "agent_name": "unknown",
                "sub_task": name,
                "status": "failure",
                "output": None,
                "error": str(e),
            }

    def _find_agent_for_task(self, task_name: str) -> Optional[str]:
        """Find which agent would handle a given task."""
        agent = self._fleet.router.route(task_name)
        if agent:
            return agent.name
        return None

    def _filter_input_for_tool(self, task_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter input data to only include keys that the target tool accepts.

        This enables safe piping of output from one tool to another even when
        the output schema does not exactly match the input schema.
        """
        agent = self._fleet.router.route(task_name)
        if agent is None:
            return input_data

        tool = agent.registry.get(task_name)
        if tool is None:
            return input_data

        try:
            sig = inspect.signature(tool.function)
            params = set(sig.parameters.keys())
            # If the tool accepts **kwargs, pass everything
            for param in sig.parameters.values():
                if param.kind == inspect.Parameter.VAR_KEYWORD:
                    return input_data
            # Filter to only accepted parameters
            filtered = {k: v for k, v in input_data.items() if k in params}
            return filtered
        except (ValueError, TypeError):
            return input_data
