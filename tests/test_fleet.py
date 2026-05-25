"""Tests for fleet management."""

import pytest

from agentwork import Agent, FleetManager, tool
from agentwork.fleet.pool import AgentPool
from agentwork.fleet.router import TaskRouter


class TestFleetManager:
    def test_register_and_dispatch(self):
        @tool(name="greet", description="Greets")
        def greet(name: str) -> str:
            return f"Hello, {name}!"

        agent = Agent(name="GreetAgent", tools=[greet])
        fleet = FleetManager()
        fleet.register(agent)

        result = fleet.dispatch("greet", {"name": "World"})
        assert result.success
        assert result.output == "Hello, World!"

    def test_dispatch_no_agent(self):
        fleet = FleetManager()
        result = fleet.dispatch("unknown_task")
        assert result.failed
        assert "No agent available" in result.error

    def test_multiple_agents(self):
        @tool(name="email", description="Send email")
        def email(to: str) -> str:
            return f"sent to {to}"

        @tool(name="report", description="Generate report")
        def report(type: str) -> str:
            return f"{type} report"

        email_agent = Agent(name="EmailAgent", tools=[email])
        report_agent = Agent(name="ReportAgent", tools=[report])

        fleet = FleetManager()
        fleet.register(email_agent)
        fleet.register(report_agent)

        r1 = fleet.dispatch("email", {"to": "test@test.com"})
        assert r1.success
        assert "sent to" in r1.output

        r2 = fleet.dispatch("report", {"type": "monthly"})
        assert r2.success
        assert "monthly" in r2.output


class TestAgentPool:
    def test_add_and_get(self):
        agent = Agent(name="TestAgent")
        pool = AgentPool()
        pool.add(agent)
        assert pool.get("TestAgent") is agent
        assert pool.size() == 1

    def test_health_tracking(self):
        agent = Agent(name="TestAgent")
        pool = AgentPool()
        pool.add(agent)
        assert pool.is_healthy("TestAgent")

        pool.mark_unhealthy("TestAgent")
        assert not pool.is_healthy("TestAgent")
        assert pool.get_healthy() == []

        pool.mark_healthy("TestAgent")
        assert pool.is_healthy("TestAgent")

    def test_remove(self):
        agent = Agent(name="TestAgent")
        pool = AgentPool()
        pool.add(agent)
        pool.remove("TestAgent")
        assert pool.get("TestAgent") is None
        assert len(pool) == 0


class TestTaskRouter:
    def test_route_by_tool_name(self):
        @tool(name="analyze", description="Analyze")
        def analyze() -> str:
            return "analyzed"

        agent = Agent(name="Analyzer", tools=[analyze])
        pool = AgentPool()
        pool.add(agent)
        router = TaskRouter(pool)

        routed = router.route("analyze")
        assert routed is agent

    def test_route_by_capability(self):
        agent = Agent(name="Worker", capabilities=["data_processing"])
        pool = AgentPool()
        pool.add(agent)
        router = TaskRouter(pool)

        routed = router.route("data_processing")
        assert routed is agent

    def test_no_route(self):
        pool = AgentPool()
        router = TaskRouter(pool)
        assert router.route("anything") is None
