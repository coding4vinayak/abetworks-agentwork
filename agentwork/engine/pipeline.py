"""Pipeline - chain tools in sequence or run in parallel."""

from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, List, Optional

from agentwork.core.result import TaskResult
from agentwork.tools.base import Tool

logger = logging.getLogger(__name__)


class Pipeline:
    """Chains tools in sequence (output of one feeds input of next).

    Also supports parallel execution of independent tools.

    Data threading note: when passing data between pipeline steps, dict outputs
    are unpacked as **kwargs into the next tool. Non-dict outputs (lists, strings,
    numbers) are passed as a single positional argument. If your tools produce
    non-dict outputs, the next tool's signature must accept exactly one positional
    parameter.

    Usage:
        pipeline = Pipeline(tools=[tool_a, tool_b, tool_c])
        result = pipeline.run(initial_input)
        # tool_a -> tool_b -> tool_c

        # Parallel execution:
        result = pipeline.run_parallel(data)
    """

    def __init__(self, tools: Optional[List[Tool]] = None) -> None:
        self.tools: List[Tool] = tools or []

    def add(self, tool: Tool) -> "Pipeline":
        """Add a tool to the pipeline. Returns self for chaining."""
        self.tools.append(tool)
        return self

    def run(self, input_data: Any = None) -> TaskResult:
        """Run tools in sequence. Each tool receives the output of the previous.

        Never raises - returns partial result if a step fails.
        """
        start_time = time.time()
        current_data = input_data
        partial_results: List[Any] = []

        for i, tool in enumerate(self.tools):
            logger.debug("Pipeline step %d: executing '%s'", i, tool.name)

            if current_data is not None and isinstance(current_data, dict):
                result = tool.execute(**current_data)
            elif current_data is not None:
                result = tool.execute(current_data)
            else:
                result = tool.execute()

            if result.success:
                current_data = result.output
                partial_results.append(result.output)
            else:
                duration_ms = (time.time() - start_time) * 1000
                return TaskResult.partial(
                    output=current_data,
                    error=f"Pipeline failed at step {i} ({tool.name}): {result.error}",
                    partial_results=partial_results,
                    duration_ms=duration_ms,
                )

        duration_ms = (time.time() - start_time) * 1000
        return TaskResult.ok(output=current_data, duration_ms=duration_ms)

    def run_parallel(self, input_data: Any = None) -> TaskResult:
        """Run all tools in parallel with the same input.

        Uses a ThreadPoolExecutor to execute tools concurrently.
        Returns a list of results from all tools.
        """
        start_time = time.time()
        results: List[Any] = [None] * len(self.tools)
        errors: List[str] = []

        def _execute_tool(index: int, tool: Tool) -> tuple:
            if input_data is not None and isinstance(input_data, dict):
                result = tool.execute(**input_data)
            elif input_data is not None:
                result = tool.execute(input_data)
            else:
                result = tool.execute()
            return index, tool.name, result

        with ThreadPoolExecutor(max_workers=len(self.tools) or 1) as executor:
            futures = [
                executor.submit(_execute_tool, i, tool)
                for i, tool in enumerate(self.tools)
            ]
            for future in as_completed(futures):
                index, tool_name, result = future.result()
                if result.success:
                    results[index] = result.output
                else:
                    errors.append(f"{tool_name}: {result.error}")

        # Filter out None placeholders for failed tools
        successful_results = [r for r in results if r is not None]

        duration_ms = (time.time() - start_time) * 1000

        if not errors:
            return TaskResult.ok(output=successful_results, duration_ms=duration_ms)
        elif not successful_results:
            return TaskResult.fail(
                error=f"All parallel tools failed: {'; '.join(errors)}",
                duration_ms=duration_ms,
            )
        else:
            return TaskResult.partial(
                output=successful_results,
                error=f"Some parallel tools failed: {'; '.join(errors)}",
                partial_results=successful_results,
                duration_ms=duration_ms,
            )

    async def run_async(self, input_data: Any = None) -> TaskResult:
        """Run tools in sequence asynchronously."""
        start_time = time.time()
        current_data = input_data
        partial_results: List[Any] = []

        for i, tool in enumerate(self.tools):
            if current_data is not None and isinstance(current_data, dict):
                result = await tool.execute_async(**current_data)
            elif current_data is not None:
                result = await tool.execute_async(current_data)
            else:
                result = await tool.execute_async()

            if result.success:
                current_data = result.output
                partial_results.append(result.output)
            else:
                duration_ms = (time.time() - start_time) * 1000
                return TaskResult.partial(
                    output=current_data,
                    error=f"Pipeline failed at step {i} ({tool.name}): {result.error}",
                    partial_results=partial_results,
                    duration_ms=duration_ms,
                )

        duration_ms = (time.time() - start_time) * 1000
        return TaskResult.ok(output=current_data, duration_ms=duration_ms)

    async def run_parallel_async(self, input_data: Any = None) -> TaskResult:
        """Run all tools in parallel asynchronously."""
        start_time = time.time()

        async def _run_tool(tool: Tool) -> TaskResult:
            if input_data is not None and isinstance(input_data, dict):
                return await tool.execute_async(**input_data)
            elif input_data is not None:
                return await tool.execute_async(input_data)
            else:
                return await tool.execute_async()

        task_results = await asyncio.gather(*[_run_tool(t) for t in self.tools])

        results: List[Any] = []
        errors: List[str] = []

        for tool, result in zip(self.tools, task_results):
            if result.success:
                results.append(result.output)
            else:
                errors.append(f"{tool.name}: {result.error}")

        duration_ms = (time.time() - start_time) * 1000

        if not errors:
            return TaskResult.ok(output=results, duration_ms=duration_ms)
        elif not results:
            return TaskResult.fail(
                error=f"All parallel tools failed: {'; '.join(errors)}",
                duration_ms=duration_ms,
            )
        else:
            return TaskResult.partial(
                output=results,
                error=f"Some parallel tools failed: {'; '.join(errors)}",
                partial_results=results,
                duration_ms=duration_ms,
            )
