"""FastAPI app factory that exposes agents over HTTP with task ID tracking.

Supports remote API communication: multiple tasks can run concurrently,
each identified by a unique task_id. Results are stored and retrievable
by task_id so responses go back to the correct requester.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

from agentwork.core.agent import Agent
from agentwork.core.result import TaskResult


class TaskRequest(BaseModel):
    """Request to execute a tool."""

    task_id: Optional[str] = Field(default=None, description="Client-specified task ID for tracking")
    tool: str = Field(..., description="Name of the tool to execute")
    input: Dict[str, Any] = Field(default_factory=dict, description="Input data for the tool")


class TaskResponse(BaseModel):
    """Response from a tool execution."""

    task_id: str = Field(..., description="Unique task ID for tracking this execution")
    status: str
    output: Any = None
    error: Optional[str] = None
    attempts: int = 1
    duration_ms: Optional[float] = None


def create_app(agent: Agent, prefix: str = "") -> Any:
    """Create a FastAPI app exposing the agent's tools over HTTP.

    The app supports concurrent task execution with ID-based tracking:
    - POST /execute - Submit a task (returns task_id for tracking)
    - GET /result/{task_id} - Retrieve result by task_id
    - GET /tools - List available tools
    - GET /health - Health check

    Args:
        agent: The Agent instance to expose.
        prefix: Optional URL prefix for all routes.

    Returns:
        FastAPI app instance.
    """
    if not HAS_FASTAPI:
        raise ImportError(
            "FastAPI is required for the server module. "
            "Install with: pip install abetworks-agentwork[server]"
        )

    app = FastAPI(
        title=f"{agent.name} API",
        description=f"HTTP API for {agent.name}: {agent.description}",
        version="2.0.0",
    )

    # In-memory storage for task results indexed by task_id
    _results_store: Dict[str, TaskResponse] = {}

    @app.get(f"{prefix}/health")
    def health() -> Dict[str, Any]:
        return {"status": "healthy", "agent": agent.name, "tools": agent.tool_names}

    @app.get(f"{prefix}/tools")
    def list_tools() -> Dict[str, Any]:
        tools_info = [
            {"name": t.name, "description": t.description, "tags": t.tags}
            for t in agent.tools
        ]
        return {"agent": agent.name, "tools": tools_info}

    @app.post(f"{prefix}/execute", response_model=TaskResponse)
    def execute_tool(request: TaskRequest) -> TaskResponse:
        """Execute a tool and store result by task_id.

        The task_id can be client-specified or auto-generated.
        Results are stored for later retrieval via GET /result/{task_id}.
        """
        task_id = request.task_id or str(uuid.uuid4())

        result = agent.execute(request.tool, request.input if request.input else None)

        response = TaskResponse(
            task_id=task_id,
            status=result.status.value,
            output=result.output,
            error=result.error,
            attempts=result.attempts,
            duration_ms=result.duration_ms,
        )

        # Store result by task_id for later retrieval
        _results_store[task_id] = response
        return response

    @app.get(f"{prefix}/result/{{task_id}}", response_model=TaskResponse)
    def get_result(task_id: str) -> TaskResponse:
        """Retrieve a stored result by task_id.

        This enables async patterns where a client submits work,
        gets back a task_id, and polls for the result later.
        """
        if task_id not in _results_store:
            raise HTTPException(
                status_code=404,
                detail=f"No result found for task_id '{task_id}'"
            )
        return _results_store[task_id]

    @app.get(f"{prefix}/results")
    def list_results() -> Dict[str, Any]:
        """List all stored task results (for management/debugging)."""
        return {
            "count": len(_results_store),
            "task_ids": list(_results_store.keys()),
        }

    return app
