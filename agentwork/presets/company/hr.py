"""HR agent preset with recruiting and people management tools."""

from __future__ import annotations

from typing import Any, Dict

from agentwork.core.agent import Agent
from agentwork.tools.decorators import tool


@tool(name="recruiter", description="Source and screen candidates for positions", retry_attempts=3)
def recruiter(position: str = "", requirements: Dict[str, Any] = None) -> Dict[str, Any]:
    """Source candidates. Override with your recruiting logic."""
    return {"position": position, "candidates_found": 0, "requirements": len(requirements or {})}


@tool(name="onboarding_manager", description="Manage employee onboarding processes", retry_attempts=3)
def onboarding_manager(employee: str = "", department: str = "") -> Dict[str, Any]:
    """Manage onboarding. Override with your onboarding logic."""
    return {"employee": employee, "department": department, "onboarding": "initiated"}


@tool(name="performance_reviewer", description="Conduct performance reviews and feedback", retry_attempts=2)
def performance_reviewer(employee: str = "", period: str = "quarterly") -> Dict[str, Any]:
    """Review performance. Override with your performance review logic."""
    return {"employee": employee, "period": period, "review": "completed"}


def HRAgent(name: str = "HRAgent", **kwargs: Any) -> Agent:
    """Create an HR agent pre-configured with human resources tools.

    Tools included:
    - recruiter: Source and screen candidates for positions
    - onboarding_manager: Manage employee onboarding processes
    - performance_reviewer: Conduct performance reviews and feedback
    """
    return Agent(
        name=name,
        description="Human resources agent for recruiting, onboarding, and performance management",
        tools=[recruiter, onboarding_manager, performance_reviewer],
        capabilities=["hiring", "onboarding", "hr", "performance"],
        **kwargs,
    )
