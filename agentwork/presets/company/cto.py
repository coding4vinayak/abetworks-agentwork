"""CTO agent preset with architecture and technology evaluation tools."""

from __future__ import annotations

from typing import Any, Dict

from agentwork.core.agent import Agent
from agentwork.tools.decorators import tool


@tool(name="architecture_designer", description="Design system architecture and infrastructure", retry_attempts=3)
def architecture_designer(system: str = "", requirements: Dict[str, Any] = None) -> Dict[str, Any]:
    """Design system architecture. Override with your architecture logic."""
    return {"system": system, "architecture": "designed", "components": len(requirements or {})}


@tool(name="tech_stack_evaluator", description="Evaluate and recommend technology stacks", retry_attempts=3)
def tech_stack_evaluator(category: str = "", constraints: Dict[str, Any] = None) -> Dict[str, Any]:
    """Evaluate technology options. Override with your evaluation logic."""
    return {"category": category, "recommendation": "evaluated", "constraints_met": True}


@tool(name="code_reviewer", description="Review code for quality, security, and best practices", retry_attempts=2)
def code_reviewer(code: str = "", language: str = "python") -> Dict[str, Any]:
    """Review code quality. Override with your code review logic."""
    return {"language": language, "review": "approved", "issues": 0}


def CTOAgent(name: str = "CTOAgent", **kwargs: Any) -> Agent:
    """Create a CTO agent pre-configured with technology leadership tools.

    Tools included:
    - architecture_designer: Design system architecture and infrastructure
    - tech_stack_evaluator: Evaluate and recommend technology stacks
    - code_reviewer: Review code for quality, security, and best practices
    """
    return Agent(
        name=name,
        description="Technology leadership agent for architecture, tech evaluation, and code review",
        tools=[architecture_designer, tech_stack_evaluator, code_reviewer],
        capabilities=["architecture", "technology", "code_review", "cto"],
        **kwargs,
    )
