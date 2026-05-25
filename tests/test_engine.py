"""Tests for the execution engine."""

import pytest

from agentwork import tool, Pipeline, TaskPlanner, TaskExecutor
from agentwork.tools.registry import ToolRegistry
from agentwork.core.result import ResultStatus


class TestPipeline:
    def test_sequential_pipeline(self):
        @tool(name="upper", description="Uppercase")
        def upper(text: str) -> str:
            return text.upper()

        @tool(name="wrap", description="Wrap")
        def wrap(text: str) -> str:
            return f"[{text}]"

        pipeline = Pipeline(tools=[upper, wrap])
        result = pipeline.run({"text": "hello"})
        assert result.success
        assert result.output == "[HELLO]"

    def test_pipeline_failure_returns_partial(self):
        @tool(name="good", description="Good")
        def good(x: int) -> int:
            return x + 1

        @tool(name="bad", description="Bad")
        def bad(x: int) -> int:
            raise ValueError("broken")

        @tool(name="after", description="After")
        def after(x: int) -> int:
            return x * 2

        pipeline = Pipeline(tools=[good, bad, after])
        result = pipeline.run({"x": 1})
        assert result.status == ResultStatus.PARTIAL
        assert "bad" in result.error

    def test_parallel_pipeline(self):
        @tool(name="a", description="A")
        def a(val: int) -> int:
            return val + 1

        @tool(name="b", description="B")
        def b(val: int) -> int:
            return val + 2

        pipeline = Pipeline(tools=[a, b])
        result = pipeline.run_parallel({"val": 10})
        assert result.success
        assert 11 in result.output
        assert 12 in result.output

    def test_add_tool(self):
        @tool(name="t", description="T")
        def t() -> str:
            return "done"

        pipeline = Pipeline()
        pipeline.add(t)
        assert len(pipeline.tools) == 1


class TestTaskPlanner:
    def test_create_plan(self):
        planner = TaskPlanner()
        plan = planner.create_plan("My plan")
        assert plan.description == "My plan"
        assert len(plan.steps) == 0

    def test_add_steps(self):
        planner = TaskPlanner()
        plan = planner.create_plan()
        s1 = plan.add_step("fetch", "data_fetcher", {"source": "db"})
        s2 = plan.add_step("process", "processor", depends_on=[s1.id])

        assert len(plan.steps) == 2
        assert s2.depends_on == [s1.id]

    def test_get_ready_steps(self):
        planner = TaskPlanner()
        plan = planner.create_plan()
        s1 = plan.add_step("first", "tool1")
        s2 = plan.add_step("second", "tool2", depends_on=[s1.id])

        # Initially only s1 is ready
        ready = plan.get_ready_steps(set())
        assert len(ready) == 1
        assert ready[0].id == s1.id

        # After s1 completes, s2 is ready
        ready = plan.get_ready_steps({s1.id})
        assert len(ready) == 1
        assert ready[0].id == s2.id


class TestTaskExecutor:
    def test_execute_plan(self):
        @tool(name="step1", description="Step 1")
        def step1(x: int) -> int:
            return x + 1

        @tool(name="step2", description="Step 2")
        def step2(y: int) -> int:
            return y * 2

        registry = ToolRegistry()
        registry.register(step1)
        registry.register(step2)

        planner = TaskPlanner()
        plan = planner.create_plan()
        s1 = plan.add_step("first", "step1", {"x": 5})
        s2 = plan.add_step("second", "step2", {"y": 10})

        executor = TaskExecutor(registry=registry)
        result = executor.execute_plan(plan)
        assert result.success

    def test_execute_plan_with_missing_tool(self):
        registry = ToolRegistry()
        planner = TaskPlanner()
        plan = planner.create_plan()
        plan.add_step("missing", "nonexistent", {})

        executor = TaskExecutor(registry=registry)
        result = executor.execute_plan(plan)
        assert result.failed
