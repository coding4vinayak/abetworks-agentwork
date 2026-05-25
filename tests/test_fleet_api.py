"""Tests for the fleet API endpoints."""

from __future__ import annotations

import pytest

from agentwork.orchestrator import CompanyOrchestrator
from agentwork.server.fleet_app import create_fleet_app
from agentwork.presets.company import DeveloperAgent, DesignerAgent


@pytest.fixture
def fleet_app():
    """Create a test fleet app with some agents."""
    orchestrator = CompanyOrchestrator(agents=[DeveloperAgent(), DesignerAgent()])
    app = create_fleet_app(orchestrator)
    return app


@pytest.fixture
def client(fleet_app):
    """Create a test client for the fleet app."""
    from fastapi.testclient import TestClient

    return TestClient(fleet_app)


class TestFleetOrchestrate:
    def test_submit_orchestration(self, client):
        """Test POST /fleet/orchestrate returns a result."""
        response = client.post("/fleet/orchestrate", json={
            "task_id": "test-orch-1",
            "task_description": "Generate code",
            "sub_tasks": [
                {"name": "code_generator", "input_data": {"spec": "hello", "language": "python"}},
            ],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-orch-1"
        assert data["status"] == "success"
        assert len(data["sub_results"]) == 1

    def test_orchestrate_auto_id(self, client):
        """Test orchestration auto-generates task_id when not provided."""
        response = client.post("/fleet/orchestrate", json={
            "task_description": "Auto ID test",
            "sub_tasks": [
                {"name": "code_generator", "input_data": {"spec": "x", "language": "python"}},
            ],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] is not None
        assert len(data["task_id"]) > 0

    def test_orchestrate_parallel(self, client):
        """Test orchestration with parallel sub-tasks."""
        response = client.post("/fleet/orchestrate", json={
            "task_id": "parallel-1",
            "task_description": "Parallel work",
            "sub_tasks": [
                {"name": "code_generator", "input_data": {"spec": "app", "language": "python"}},
                {"name": "ui_designer", "input_data": {"page": "home", "style": "modern"}},
            ],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["sub_results"]) == 2


class TestFleetResult:
    def test_get_result(self, client):
        """Test GET /fleet/result/{task_id} retrieves stored result."""
        # First submit a task
        client.post("/fleet/orchestrate", json={
            "task_id": "result-test-1",
            "task_description": "Store result",
            "sub_tasks": [
                {"name": "code_generator", "input_data": {"spec": "y", "language": "python"}},
            ],
        })

        # Then retrieve the result
        response = client.get("/fleet/result/result-test-1")
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "result-test-1"
        assert data["status"] == "success"

    def test_get_result_not_found(self, client):
        """Test GET /fleet/result/{task_id} returns 404 for unknown ID."""
        response = client.get("/fleet/result/nonexistent-id")
        assert response.status_code == 404


class TestFleetStatus:
    def test_get_status(self, client):
        """Test GET /fleet/status/{task_id} returns status."""
        client.post("/fleet/orchestrate", json={
            "task_id": "status-test-1",
            "task_description": "Status check",
            "sub_tasks": [
                {"name": "code_generator", "input_data": {"spec": "z", "language": "python"}},
            ],
        })

        response = client.get("/fleet/status/status-test-1")
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "status-test-1"
        assert data["status"] == "success"

    def test_get_status_not_found(self, client):
        """Test GET /fleet/status/{task_id} returns 404 for unknown ID."""
        response = client.get("/fleet/status/unknown-id")
        assert response.status_code == 404


class TestFleetAgents:
    def test_list_agents(self, client):
        """Test GET /fleet/agents lists registered agents."""
        response = client.get("/fleet/agents")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        agent_names = [a["name"] for a in data["agents"]]
        assert "DeveloperAgent" in agent_names
        assert "DesignerAgent" in agent_names

    def test_register_agent(self, client):
        """Test POST /fleet/agents registers a new agent."""
        response = client.post("/fleet/agents", json={
            "agent_name": "TestAgent",
            "capabilities": ["testing"],
            "tools": [],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "registered"
        assert data["agent_name"] == "TestAgent"

        # Verify agent is now listed
        response = client.get("/fleet/agents")
        data = response.json()
        assert data["count"] == 3

    def test_remove_agent(self, client):
        """Test DELETE /fleet/agents/{agent_name} removes an agent."""
        response = client.delete("/fleet/agents/DeveloperAgent")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "removed"

        # Verify agent is gone
        response = client.get("/fleet/agents")
        data = response.json()
        assert data["count"] == 1

    def test_remove_nonexistent_agent(self, client):
        """Test DELETE /fleet/agents/{agent_name} returns 404 for unknown agent."""
        response = client.delete("/fleet/agents/NonexistentAgent")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower() or "NonexistentAgent" in data["detail"]


class TestFleetApiAuth:
    def test_api_key_auth_blocks_unauthenticated(self):
        """Test that api_keys parameter enables auth on fleet endpoints."""
        from fastapi.testclient import TestClient

        orchestrator = CompanyOrchestrator(agents=[DeveloperAgent()])
        app = create_fleet_app(orchestrator, api_keys=["secret-key-123"])
        client = TestClient(app)

        # Request without API key should be rejected
        response = client.get("/fleet/agents")
        assert response.status_code == 401

    def test_api_key_auth_allows_authenticated(self):
        """Test that a valid API key grants access."""
        from fastapi.testclient import TestClient

        orchestrator = CompanyOrchestrator(agents=[DeveloperAgent()])
        app = create_fleet_app(orchestrator, api_keys=["secret-key-123"])
        client = TestClient(app)

        # Request with valid API key should succeed
        response = client.get("/fleet/agents", headers={"X-API-Key": "secret-key-123"})
        assert response.status_code == 200
