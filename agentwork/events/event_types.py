"""Typed event definitions for the EventBus."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """Base event with common fields for all events."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = "base"


class TaskStarted(BaseEvent):
    """Fired when a task begins execution."""

    event_type: str = "task.started"
    task_id: str
    agent_name: str = ""


class TaskCompleted(BaseEvent):
    """Fired when a task completes successfully."""

    event_type: str = "task.completed"
    task_id: str
    agent_name: str = ""
    output: Any = None


class TaskFailed(BaseEvent):
    """Fired when a task fails."""

    event_type: str = "task.failed"
    task_id: str
    agent_name: str = ""
    error: str = ""


class AgentHealthChanged(BaseEvent):
    """Fired when an agent's health status changes."""

    event_type: str = "agent.health_changed"
    agent_name: str
    status: str


class CustomEvent(BaseEvent):
    """User-defined event with configurable event_type."""

    event_type: str = "custom"
    data: Any = None
