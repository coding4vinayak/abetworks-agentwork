"""CEO agent preset with strategic planning and delegation tools."""

from __future__ import annotations

from typing import Any, Dict

from agentwork.core.agent import Agent
from agentwork.tools.decorators import tool


@tool(name="strategic_planning", description="Develop strategic plans and roadmaps", retry_attempts=3)
def strategic_planning(goal: str = "", timeline: str = "quarterly") -> Dict[str, Any]:
    """Create strategic plans. Override with your actual planning logic."""
    return {"plan": goal, "timeline": timeline, "status": "drafted"}


@tool(name="decision_maker", description="Evaluate options and make executive decisions", retry_attempts=3)
def decision_maker(options: Dict[str, Any] = None, criteria: str = "") -> Dict[str, Any]:
    """Make executive decisions. Override with your decision logic."""
    return {"decision": "approved", "options_evaluated": len(options or {}), "criteria": criteria}


@tool(name="task_delegator", description="Delegate tasks to appropriate team members", retry_attempts=2)
def task_delegator(task: str = "", assignee: str = "", priority: str = "medium") -> Dict[str, Any]:
    """Delegate tasks to team. Override with your delegation logic."""
    return {"task": task, "assignee": assignee, "priority": priority, "status": "delegated"}


def CEOAgent(name: str = "CEOAgent", **kwargs: Any) -> Agent:
    """Create a CEO agent pre-configured with executive leadership tools.

    Tools included:
    - strategic_planning: Develop strategic plans and roadmaps
    - decision_maker: Evaluate options and make executive decisions
    - task_delegator: Delegate tasks to appropriate team members
    """
    return Agent(
        name=name,
        description="Executive leadership agent for strategy, decisions, and delegation",
        tools=[strategic_planning, decision_maker, task_delegator],
        capabilities=["strategy", "delegation", "leadership", "ceo"],
        **kwargs,
    )
