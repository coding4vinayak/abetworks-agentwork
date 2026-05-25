"""Execution context that carries state through tool execution."""

from __future__ import annotations

import uuid
from typing import Any, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class ExecutionContext(BaseModel):
    """Carries state through a chain of tool executions.

    Provides a way to pass data between tools, track execution history,
    and maintain metadata about the current execution run.

    Known limitation: This context is currently created in Agent.execute() and
    records start/end events, but it is not passed into tools or returned on the
    TaskResult. The context object is effectively lost after execution completes.
    Future work will wire the context through the tool layer and store it on
    the result, enabling nested agent calls to share state via child contexts.
    """

    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: Optional[str] = None
    agent_name: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    state: dict[str, Any] = Field(default_factory=dict)
    history: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    parent_context_id: Optional[str] = None

    def set(self, key: str, value: Any) -> None:
        """Set a value in the execution state."""
        self.state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the execution state."""
        return self.state.get(key, default)

    def record(self, event: str, data: Optional[dict[str, Any]] = None) -> None:
        """Record an event in the execution history."""
        entry = {
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {},
        }
        self.history.append(entry)

    def child(self, task_id: Optional[str] = None) -> ExecutionContext:
        """Create a child context inheriting state from this context."""
        return ExecutionContext(
            task_id=task_id or self.task_id,
            agent_name=self.agent_name,
            state=dict(self.state),
            metadata=dict(self.metadata),
            parent_context_id=self.execution_id,
        )
