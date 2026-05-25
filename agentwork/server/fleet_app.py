"""Fleet API app factory for remote orchestration with task-ID tracking.

Supports multiple concurrent orchestrations, each identified by a unique
task_id. Results are stored and retrievable by task_id so responses go
back to the correct requester only.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

from agentwork.orchestrator import CompanyOrchestrator, CompanyTaskResult
from agentwork.server.app import LRUResultStore, DEFAULT_MAX_RESULTS


class OrchestrationRequest(BaseModel):
    """Request to submit an orchestration task."""

    task_id: Optional[str] = Field(default=None, description="Client-specified task ID for tracking")
    task_description: str = Field(..., description="Human-readable description of the task")
    sub_tasks: List[Dict[str, Any]] = Field(..., description="List of sub-task definitions")
    input_data: Optional[Dict[str, Any]] = Field(default=None, description="Shared input data")


class AgentRegistrationRequest(BaseModel):
    """Request to register a new agent."""

    agent_name: str = Field(..., description="Name of the agent")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    tools: List[str] = Field(default_factory=list, description="Tool names for the agent")


def create_fleet_app(
    orchestrator: CompanyOrchestrator,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> Any:
    """Create a FastAPI app exposing fleet orchestration over HTTP.

    Endpoints support remote API communication with task-ID tracking:
    - POST /fleet/orchestrate - Submit orchestration (returns CompanyTaskResult)
    - GET /fleet/status/{task_id} - Get orchestration status
    - GET /fleet/result/{task_id} - Get final result by task_id
    - GET /fleet/agents - List all registered agents
    - POST /fleet/agents - Register a new agent
    - DELETE /fleet/agents/{agent_name} - Remove an agent

    Args:
        orchestrator: The CompanyOrchestrator instance to expose.
        max_results: Maximum number of results to keep in memory.

    Returns:
        FastAPI app instance.
    """
    if not HAS_FASTAPI:
        raise ImportError(
            "FastAPI is required for the server module. "
            "Install with: pip install abetworks-agentwork[server]"
        )

    app = FastAPI(
        title="Fleet Orchestration API",
        description="HTTP API for multi-agent orchestration with task-ID tracking",
        version="2.0.0",
    )

    _results_store = LRUResultStore(max_size=max_results)

    @app.post("/fleet/orchestrate")
    def orchestrate(request: OrchestrationRequest) -> Dict[str, Any]:
        """Submit an orchestration task and get the result.

        Runs synchronously and stores the result by task_id for later retrieval.
        """
        task_id = request.task_id or str(uuid.uuid4())

        result = orchestrator.orchestrate(
            task_description=request.task_description,
            sub_tasks=request.sub_tasks,
            input_data=request.input_data,
            task_id=task_id,
        )

        _results_store.put(task_id, result)

        return result.model_dump()

    @app.get("/fleet/status/{task_id}")
    def get_status(task_id: str) -> Dict[str, Any]:
        """Get orchestration status by task_id."""
        status = orchestrator.get_status(task_id)
        if status is None:
            raise HTTPException(
                status_code=404,
                detail=f"No orchestration found for task_id '{task_id}'",
            )
        return status

    @app.get("/fleet/result/{task_id}")
    def get_result(task_id: str) -> Dict[str, Any]:
        """Get final result by task_id. Only returns the result for the specified ID."""
        result = _results_store.get(task_id)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"No result found for task_id '{task_id}'",
            )
        if isinstance(result, BaseModel):
            return result.model_dump()
        return result

    @app.get("/fleet/agents")
    def list_agents() -> Dict[str, Any]:
        """List all registered agents with their capabilities."""
        agents_info = []
        for agent in orchestrator.agents:
            agents_info.append({
                "name": agent.name,
                "description": agent.description,
                "capabilities": agent.capabilities,
                "tools": agent.tool_names,
            })
        return {"agents": agents_info, "count": len(agents_info)}

    @app.post("/fleet/agents")
    def register_agent(request: AgentRegistrationRequest) -> Dict[str, Any]:
        """Register a new agent dynamically."""
        from agentwork.core.agent import Agent

        agent = Agent(
            name=request.agent_name,
            capabilities=request.capabilities,
        )
        orchestrator.add_agent(agent)
        return {"status": "registered", "agent_name": request.agent_name}

    @app.delete("/fleet/agents/{agent_name}")
    def remove_agent(agent_name: str) -> Dict[str, Any]:
        """Remove an agent from the fleet."""
        try:
            orchestrator.remove_agent(agent_name)
            return {"status": "removed", "agent_name": agent_name}
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{agent_name}' not found: {str(e)}",
            )

    return app
