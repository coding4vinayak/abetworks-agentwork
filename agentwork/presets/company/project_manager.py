"""Project manager agent preset with planning and tracking tools."""

from __future__ import annotations

from typing import Any, Dict

from agentwork.core.agent import Agent
from agentwork.tools.decorators import tool


@tool(name="task_tracker", description="Track and manage project tasks", retry_attempts=3)
def task_tracker(task: str = "", status: str = "open") -> Dict[str, Any]:
    """Track project tasks. Override with your task tracking logic."""
    return {"task": task, "status": status, "tracked": True}


@tool(name="timeline_planner", description="Plan project timelines and milestones", retry_attempts=3)
def timeline_planner(project: str = "", duration: str = "1 month") -> Dict[str, Any]:
    """Plan project timelines. Override with your timeline planning logic."""
    return {"project": project, "duration": duration, "timeline": "planned"}


@tool(name="status_reporter", description="Generate project status reports", retry_attempts=2)
def status_reporter(project: str = "", format: str = "summary") -> Dict[str, Any]:
    """Generate status reports. Override with your reporting logic."""
    return {"project": project, "format": format, "report": "generated"}


def ProjectManagerAgent(name: str = "ProjectManagerAgent", **kwargs: Any) -> Agent:
    """Create a project manager agent pre-configured with project management tools.

    Tools included:
    - task_tracker: Track and manage project tasks
    - timeline_planner: Plan project timelines and milestones
    - status_reporter: Generate project status reports
    """
    return Agent(
        name=name,
        description="Project management agent for task tracking, timeline planning, and status reporting",
        tools=[task_tracker, timeline_planner, status_reporter],
        capabilities=["project_management", "planning", "tracking", "status"],
        **kwargs,
    )
