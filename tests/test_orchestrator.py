"""Tests for the CompanyOrchestrator."""

from __future__ import annotations

import pytest

from agentwork.orchestrator import CompanyOrchestrator, CompanyTaskResult
from agentwork.presets.company import (
    CEOAgent,
    CTOAgent,
    DeveloperAgent,
    DesignerAgent,
    ProjectManagerAgent,
)


class TestCompanyOrchestrator:
    def test_basic_orchestration(self):
        """Test a simple orchestration with a single sub-task."""
        orchestrator = CompanyOrchestrator(agents=[DeveloperAgent()])
        result = orchestrator.orchestrate(
            task_description="Generate some code",
            sub_tasks=[
                {"name": "code_generator", "input_data": {"spec": "hello", "language": "python"}},
            ],
        )
        assert isinstance(result, CompanyTaskResult)
        assert result.status == "success"
        assert len(result.sub_results) == 1
        assert result.sub_results[0]["status"] == "success"
        assert result.duration_ms > 0

    def test_sequential_piping(self):
        """Test sub-tasks with dependencies pipe output to the next."""
        orchestrator = CompanyOrchestrator(agents=[CEOAgent()])
        # strategic_planning returns {"plan": ..., "timeline": ..., "status": "drafted"}
        # task_delegator accepts (task="", assignee="", priority="medium")
        # The orchestrator filters piped output to matching params only.
        # Since "status" is not a param of task_delegator, it is filtered out.
        # task_delegator will run with its defaults since no output keys match.
        result = orchestrator.orchestrate(
            task_description="Plan then delegate",
            sub_tasks=[
                {"name": "strategic_planning", "input_data": {"goal": "launch product", "timeline": "q1"}},
                {"name": "task_delegator", "depends_on": ["strategic_planning"]},
            ],
        )
        assert result.status == "success"
        assert len(result.sub_results) == 2
        assert result.sub_results[0]["sub_task"] == "strategic_planning"
        assert result.sub_results[1]["sub_task"] == "task_delegator"
        assert result.sub_results[1]["status"] == "success"

    def test_parallel_execution(self):
        """Test independent sub-tasks run in parallel."""
        orchestrator = CompanyOrchestrator(
            agents=[DeveloperAgent(), DesignerAgent()]
        )
        result = orchestrator.orchestrate(
            task_description="Develop and design in parallel",
            sub_tasks=[
                {"name": "code_generator", "input_data": {"spec": "app", "language": "python"}},
                {"name": "ui_designer", "input_data": {"page": "home", "style": "modern"}},
            ],
        )
        assert result.status == "success"
        assert len(result.sub_results) == 2

    def test_mixed_dag_execution(self):
        """Test a DAG with both parallel and sequential steps."""
        orchestrator = CompanyOrchestrator(
            agents=[CEOAgent(), ProjectManagerAgent()]
        )
        result = orchestrator.orchestrate(
            task_description="Plan then track then report",
            sub_tasks=[
                {"name": "strategic_planning", "input_data": {"goal": "launch", "timeline": "q1"}},
                {"name": "task_tracker", "input_data": {"task": "feature", "status": "open"}},
                {"name": "status_reporter", "depends_on": ["strategic_planning", "task_tracker"]},
            ],
        )
        assert result.status == "success"
        assert len(result.sub_results) == 3
        # The first two run in parallel, the third depends on both
        assert result.sub_results[2]["sub_task"] == "status_reporter"

    def test_agent_failure_returns_partial(self):
        """Test that when an agent fails, the orchestrator returns partial results."""
        orchestrator = CompanyOrchestrator(agents=[DeveloperAgent()])
        # 'nonexistent_tool' will fail because no agent has it
        result = orchestrator.orchestrate(
            task_description="Try tasks where one will fail",
            sub_tasks=[
                {"name": "code_generator", "input_data": {"spec": "ok", "language": "python"}},
                {"name": "nonexistent_tool", "input_data": {"data": "test"}},
            ],
        )
        assert result.status == "partial"
        statuses = [r["status"] for r in result.sub_results]
        assert "success" in statuses
        assert "failure" in statuses

    def test_all_failures_return_failure(self):
        """Test that if all sub-tasks fail, status is failure."""
        orchestrator = CompanyOrchestrator(agents=[DeveloperAgent()])
        result = orchestrator.orchestrate(
            task_description="All will fail",
            sub_tasks=[
                {"name": "nonexistent_1", "input_data": {}},
                {"name": "nonexistent_2", "input_data": {}},
            ],
        )
        assert result.status == "failure"

    def test_task_id_tracking(self):
        """Test that orchestrations are tracked by task_id."""
        orchestrator = CompanyOrchestrator(agents=[DeveloperAgent()])
        result = orchestrator.orchestrate(
            task_description="Tracked task",
            sub_tasks=[
                {"name": "code_generator", "input_data": {"spec": "x", "language": "python"}},
            ],
            task_id="my-task-123",
        )
        assert result.task_id == "my-task-123"
        status = orchestrator.get_status("my-task-123")
        assert status is not None
        assert status["status"] == "success"

    def test_auto_generated_task_id(self):
        """Test that a task_id is auto-generated if not provided."""
        orchestrator = CompanyOrchestrator(agents=[DeveloperAgent()])
        result = orchestrator.orchestrate(
            task_description="Auto ID task",
            sub_tasks=[
                {"name": "code_generator", "input_data": {"spec": "y", "language": "python"}},
            ],
        )
        assert result.task_id is not None
        assert len(result.task_id) > 0

    def test_add_and_remove_agent(self):
        """Test adding and removing agents."""
        orchestrator = CompanyOrchestrator()
        assert len(orchestrator.agents) == 0

        dev = DeveloperAgent()
        orchestrator.add_agent(dev)
        assert len(orchestrator.agents) == 1

        orchestrator.remove_agent("DeveloperAgent")
        assert len(orchestrator.agents) == 0

    def test_get_status_unknown_id(self):
        """Test get_status returns None for unknown task_id."""
        orchestrator = CompanyOrchestrator()
        assert orchestrator.get_status("unknown-id") is None


class TestCompanyOrchestratorAsync:
    @pytest.mark.asyncio
    async def test_async_orchestration(self):
        """Test async orchestration works."""
        orchestrator = CompanyOrchestrator(agents=[DeveloperAgent()])
        result = await orchestrator.orchestrate_async(
            task_description="Async task",
            sub_tasks=[
                {"name": "code_generator", "input_data": {"spec": "async", "language": "python"}},
            ],
            task_id="async-task-1",
        )
        assert result.status == "success"
        assert result.task_id == "async-task-1"

    @pytest.mark.asyncio
    async def test_async_parallel(self):
        """Test async orchestration with parallel sub-tasks."""
        orchestrator = CompanyOrchestrator(
            agents=[DeveloperAgent(), DesignerAgent()]
        )
        result = await orchestrator.orchestrate_async(
            task_description="Async parallel",
            sub_tasks=[
                {"name": "code_generator", "input_data": {"spec": "app", "language": "python"}},
                {"name": "ui_designer", "input_data": {"page": "home", "style": "modern"}},
            ],
        )
        assert result.status == "success"
        assert len(result.sub_results) == 2

    @pytest.mark.asyncio
    async def test_async_sequential(self):
        """Test async orchestration with sequential dependencies."""
        orchestrator = CompanyOrchestrator(agents=[CEOAgent()])
        result = await orchestrator.orchestrate_async(
            task_description="Async sequential",
            sub_tasks=[
                {"name": "strategic_planning", "input_data": {"goal": "grow", "timeline": "q2"}},
                {"name": "task_delegator", "depends_on": ["strategic_planning"]},
            ],
        )
        assert result.status == "success"
        assert len(result.sub_results) == 2
