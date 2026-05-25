"""Tests for core agent functionality."""

import pytest

from agentwork import Agent, tool, TaskResult
from agentwork.core.context import ExecutionContext
from agentwork.core.exceptions import AgentError, ToolError, RetryableError, FatalError, TimeoutError
from agentwork.core.result import ResultStatus


class TestAgent:
    def test_create_agent(self):
        agent = Agent(name="TestAgent", description="A test agent")
        assert agent.name == "TestAgent"
        assert agent.description == "A test agent"
        assert agent.tools == []

    def test_agent_with_tools(self):
        @tool(name="greet", description="Greets")
        def greet(name: str) -> str:
            return f"Hello, {name}!"

        agent = Agent(name="TestAgent", tools=[greet])
        assert "greet" in agent.tool_names

    def test_execute_tool(self):
        @tool(name="greet", description="Greets")
        def greet(name: str) -> str:
            return f"Hello, {name}!"

        agent = Agent(name="TestAgent", tools=[greet])
        result = agent.execute("greet", {"name": "World"})
        assert result.success
        assert result.output == "Hello, World!"
        assert result.status == ResultStatus.SUCCESS

    def test_execute_missing_tool(self):
        agent = Agent(name="TestAgent")
        result = agent.execute("nonexistent", {"data": "test"})
        assert result.failed
        assert "not found" in result.error

    def test_execution_history(self):
        @tool(name="add", description="Adds")
        def add(a: int, b: int) -> int:
            return a + b

        agent = Agent(name="TestAgent", tools=[add])
        agent.execute("add", {"a": 1, "b": 2})
        agent.execute("add", {"a": 3, "b": 4})

        assert len(agent.execution_history) == 2
        assert agent.execution_history[0]["status"] == "success"

    def test_add_and_remove_tool(self):
        @tool(name="t1", description="Tool 1")
        def t1() -> str:
            return "t1"

        agent = Agent(name="TestAgent")
        agent.add_tool(t1)
        assert "t1" in agent.tool_names

        agent.remove_tool("t1")
        assert "t1" not in agent.tool_names


class TestAsyncAgent:
    @pytest.mark.asyncio
    async def test_async_execute(self):
        @tool(name="greet", description="Greets")
        def greet(name: str) -> str:
            return f"Hello, {name}!"

        agent = Agent(name="TestAgent", tools=[greet])
        result = await agent.execute_async("greet", {"name": "Async"})
        assert result.success
        assert result.output == "Hello, Async!"


class TestTaskResult:
    def test_success_result(self):
        result = TaskResult.ok(output="data")
        assert result.success
        assert not result.failed
        assert result.output == "data"

    def test_failure_result(self):
        result = TaskResult.fail(error="something broke")
        assert result.failed
        assert not result.success
        assert result.error == "something broke"

    def test_partial_result(self):
        result = TaskResult.partial(output="partial", error="some failed")
        assert result.status == ResultStatus.PARTIAL
        assert result.output == "partial"
        assert result.error == "some failed"


class TestExecutionContext:
    def test_context_state(self):
        ctx = ExecutionContext()
        ctx.set("key", "value")
        assert ctx.get("key") == "value"
        assert ctx.get("missing", "default") == "default"

    def test_context_record(self):
        ctx = ExecutionContext()
        ctx.record("started", {"task": "test"})
        assert len(ctx.history) == 1
        assert ctx.history[0]["event"] == "started"

    def test_child_context(self):
        ctx = ExecutionContext(agent_name="parent")
        ctx.set("shared", "data")
        child = ctx.child(task_id="child_task")
        assert child.parent_context_id == ctx.execution_id
        assert child.get("shared") == "data"
        assert child.agent_name == "parent"


class TestExceptions:
    def test_agent_error(self):
        err = AgentError("test error", details={"key": "value"})
        assert str(err) == "test error"
        assert err.details == {"key": "value"}

    def test_tool_error(self):
        err = ToolError("tool failed", tool_name="my_tool")
        assert err.tool_name == "my_tool"

    def test_retryable_error(self):
        err = RetryableError("retry me", attempts_remaining=3)
        assert err.attempts_remaining == 3

    def test_fatal_error(self):
        err = FatalError("fatal")
        assert str(err) == "fatal"

    def test_timeout_error(self):
        err = TimeoutError(timeout_seconds=5.0)
        assert err.timeout_seconds == 5.0
