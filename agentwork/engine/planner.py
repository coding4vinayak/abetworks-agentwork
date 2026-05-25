"""Task planner - breaks complex tasks into ordered steps."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Step(BaseModel):
    """A single step in a task plan."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    tool_name: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    retry_attempts: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskPlan(BaseModel):
    """A plan consisting of ordered steps."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    steps: List[Step] = Field(default_factory=list)

    def add_step(
        self,
        name: str,
        tool_name: str,
        input_data: Optional[Dict[str, Any]] = None,
        depends_on: Optional[List[str]] = None,
        retry_attempts: int = 0,
    ) -> Step:
        """Add a step to the plan."""
        step = Step(
            name=name,
            tool_name=tool_name,
            input_data=input_data or {},
            depends_on=depends_on or [],
            retry_attempts=retry_attempts,
        )
        self.steps.append(step)
        return step

    def get_ready_steps(self, completed_ids: set[str]) -> List[Step]:
        """Get steps whose dependencies are all met."""
        return [
            s
            for s in self.steps
            if s.id not in completed_ids
            and all(dep in completed_ids for dep in s.depends_on)
        ]


class TaskPlanner:
    """Plans task execution by breaking high-level tasks into steps.

    Usage:
        planner = TaskPlanner()
        plan = planner.create_plan("Process and send report")
        plan.add_step("fetch_data", "data_fetcher", {"source": "db"})
        plan.add_step("format", "formatter", depends_on=[step1.id])
    """

    def __init__(self) -> None:
        self._plans: Dict[str, TaskPlan] = {}

    def create_plan(self, description: str = "") -> TaskPlan:
        """Create a new task plan."""
        plan = TaskPlan(description=description)
        self._plans[plan.id] = plan
        return plan

    def get_plan(self, plan_id: str) -> Optional[TaskPlan]:
        """Retrieve a plan by ID."""
        return self._plans.get(plan_id)

    def list_plans(self) -> List[TaskPlan]:
        """List all plans."""
        return list(self._plans.values())
