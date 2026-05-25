"""BaseAgent and Agent classes - the core of the framework."""

from __future__ import annotations

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from agentwork.core.context import ExecutionContext
from agentwork.core.result import TaskResult
from agentwork.tools.base import Tool
from agentwork.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    @abstractmethod
    def execute(self, task: str, input_data: Optional[Dict[str, Any]] = None) -> TaskResult:
        """Execute a task. Must be implemented by subclasses."""
        ...

    @abstractmethod
    async def execute_async(
        self, task: str, input_data: Optional[Dict[str, Any]] = None
    ) -> TaskResult:
        """Execute a task asynchronously. Must be implemented by subclasses."""
        ...


class Agent(BaseAgent):
    """Production-grade agent that executes tools with retry and recovery.

    Usage:
        from agentwork import Agent, tool

        @tool(name="greet", description="Greets a person")
        def greet(name: str) -> str:
            return f"Hello, {name}!"

        agent = Agent(name="MyAgent", tools=[greet])
        result = agent.execute("greet", {"name": "World"})
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        tools: Optional[List[Tool]] = None,
        capabilities: Optional[List[str]] = None,
    ) -> None:
        self.name = name
        self.description = description
        self.capabilities = capabilities or []
        self.registry = ToolRegistry()
        self._execution_history: List[Dict[str, Any]] = []
        self._id = str(uuid.uuid4())

        if tools:
            for t in tools:
                self.registry.register(t)

    @property
    def id(self) -> str:
        return self._id

    @property
    def tools(self) -> List[Tool]:
        """List all registered tools."""
        return self.registry.list_tools()

    @property
    def tool_names(self) -> List[str]:
        """List all registered tool names."""
        return self.registry.list_names()

    @property
    def execution_history(self) -> List[Dict[str, Any]]:
        """Access the execution history."""
        return list(self._execution_history)

    def add_tool(self, tool: Tool) -> None:
        """Add a tool to this agent."""
        self.registry.register(tool)

    def remove_tool(self, name: str) -> Optional[Tool]:
        """Remove a tool from this agent by name."""
        return self.registry.unregister(name)

    def execute(
        self, task: str, input_data: Optional[Dict[str, Any]] = None
    ) -> TaskResult:
        """Execute a named tool with the given input data.

        Never raises - returns a TaskResult with status and error info if anything fails.
        """
        context = ExecutionContext(
            task_id=str(uuid.uuid4()),
            agent_name=self.name,
        )
        context.record("execution_started", {"task": task, "input": input_data})

        tool = self.registry.get(task)
        if tool is None:
            result = TaskResult.fail(
                error=f"Tool '{task}' not found. Available tools: {self.tool_names}"
            )
            self._record_execution(task, input_data, result, context)
            return result

        try:
            if input_data:
                result = tool.execute(**input_data)
            else:
                result = tool.execute()
        except Exception as e:
            logger.error("Unexpected error executing tool '%s': %s", task, str(e))
            result = TaskResult.fail(
                error=f"Unexpected error: {str(e)}",
                error_details={"exception_type": type(e).__name__},
            )

        self._record_execution(task, input_data, result, context)
        context.record("execution_completed", {"status": result.status.value})
        return result

    async def execute_async(
        self, task: str, input_data: Optional[Dict[str, Any]] = None
    ) -> TaskResult:
        """Execute a named tool asynchronously.

        Never raises - returns a TaskResult with status and error info if anything fails.
        """
        context = ExecutionContext(
            task_id=str(uuid.uuid4()),
            agent_name=self.name,
        )
        context.record("async_execution_started", {"task": task, "input": input_data})

        tool = self.registry.get(task)
        if tool is None:
            result = TaskResult.fail(
                error=f"Tool '{task}' not found. Available tools: {self.tool_names}"
            )
            self._record_execution(task, input_data, result, context)
            return result

        try:
            if input_data:
                result = await tool.execute_async(**input_data)
            else:
                result = await tool.execute_async()
        except Exception as e:
            logger.error("Unexpected async error executing tool '%s': %s", task, str(e))
            result = TaskResult.fail(
                error=f"Unexpected error: {str(e)}",
                error_details={"exception_type": type(e).__name__},
            )

        self._record_execution(task, input_data, result, context)
        context.record("async_execution_completed", {"status": result.status.value})
        return result

    def _record_execution(
        self,
        task: str,
        input_data: Optional[Dict[str, Any]],
        result: TaskResult,
        context: ExecutionContext,
    ) -> None:
        """Record execution in history for observability."""
        self._execution_history.append(
            {
                "task": task,
                "input": input_data,
                "status": result.status.value,
                "output": result.output,
                "error": result.error,
                "context_id": context.execution_id,
            }
        )
