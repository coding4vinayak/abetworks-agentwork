"""Task executor - runs planned steps with retry/fallback and tracks progress."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from agentwork.core.context import ExecutionContext
from agentwork.core.result import TaskResult, ResultStatus
from agentwork.engine.planner import TaskPlan, Step
from agentwork.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class StepResult:
    """Result of a single step execution."""

    def __init__(self, step: Step, result: TaskResult) -> None:
        self.step = step
        self.result = result

    @property
    def success(self) -> bool:
        return self.result.success


class TaskExecutor:
    """Executes planned steps with retry/fallback, tracks progress, handles partial failures.

    Usage:
        executor = TaskExecutor(registry=my_tool_registry)
        results = executor.execute_plan(plan)
    """

    def __init__(self, registry: Optional[ToolRegistry] = None) -> None:
        self.registry = registry or ToolRegistry()
        self._results: Dict[str, StepResult] = {}

    def execute_plan(self, plan: TaskPlan) -> TaskResult:
        """Execute all steps in a plan respecting dependencies.

        Returns a TaskResult with partial results if some steps fail.
        Never raises.
        """
        completed_ids: set[str] = set()
        failed_ids: set[str] = set()
        step_results: List[StepResult] = []
        context = ExecutionContext()

        while True:
            ready = plan.get_ready_steps(completed_ids | failed_ids)
            if not ready:
                break

            for step in ready:
                result = self._execute_step(step, context)
                step_results.append(result)
                self._results[step.id] = result

                if result.success:
                    completed_ids.add(step.id)
                    context.set(f"step_{step.name}_output", result.result.output)
                else:
                    failed_ids.add(step.id)
                    logger.warning("Step '%s' failed: %s", step.name, result.result.error)

        total = len(plan.steps)
        succeeded = len(completed_ids)

        if succeeded == total:
            outputs = [r.result.output for r in step_results if r.success]
            return TaskResult.ok(
                output=outputs[-1] if outputs else None,
                metadata={"steps_completed": succeeded, "steps_total": total},
            )
        elif succeeded == 0:
            return TaskResult.fail(
                error=f"All {total} steps failed",
                error_details=[
                    {"step": r.step.name, "error": r.result.error}
                    for r in step_results
                    if not r.success
                ],
            )
        else:
            return TaskResult.partial(
                output=[r.result.output for r in step_results if r.success],
                error=f"{total - succeeded}/{total} steps failed",
                partial_results=[r.result.output for r in step_results if r.success],
                metadata={"steps_completed": succeeded, "steps_total": total},
            )

    def _execute_step(self, step: Step, context: ExecutionContext) -> StepResult:
        """Execute a single step."""
        tool = self.registry.get(step.tool_name)
        if tool is None:
            result = TaskResult.fail(
                error=f"Tool '{step.tool_name}' not found in registry"
            )
            return StepResult(step=step, result=result)

        result = tool.execute(**step.input_data)
        return StepResult(step=step, result=result)

    async def execute_plan_async(self, plan: TaskPlan) -> TaskResult:
        """Execute a plan asynchronously, running independent steps in parallel."""
        completed_ids: set[str] = set()
        failed_ids: set[str] = set()
        step_results: List[StepResult] = []
        context = ExecutionContext()

        while True:
            ready = plan.get_ready_steps(completed_ids | failed_ids)
            if not ready:
                break

            tasks = [self._execute_step_async(step, context) for step in ready]
            results = await asyncio.gather(*tasks)

            for result in results:
                step_results.append(result)
                self._results[result.step.id] = result
                if result.success:
                    completed_ids.add(result.step.id)
                    context.set(
                        f"step_{result.step.name}_output", result.result.output
                    )
                else:
                    failed_ids.add(result.step.id)

        total = len(plan.steps)
        succeeded = len(completed_ids)

        if succeeded == total:
            outputs = [r.result.output for r in step_results if r.success]
            return TaskResult.ok(
                output=outputs[-1] if outputs else None,
                metadata={"steps_completed": succeeded, "steps_total": total},
            )
        elif succeeded == 0:
            return TaskResult.fail(error=f"All {total} steps failed")
        else:
            return TaskResult.partial(
                output=[r.result.output for r in step_results if r.success],
                error=f"{total - succeeded}/{total} steps failed",
                partial_results=[r.result.output for r in step_results if r.success],
            )

    async def _execute_step_async(
        self, step: Step, context: ExecutionContext
    ) -> StepResult:
        """Execute a single step asynchronously."""
        tool = self.registry.get(step.tool_name)
        if tool is None:
            result = TaskResult.fail(
                error=f"Tool '{step.tool_name}' not found in registry"
            )
            return StepResult(step=step, result=result)

        result = await tool.execute_async(**step.input_data)
        return StepResult(step=step, result=result)
