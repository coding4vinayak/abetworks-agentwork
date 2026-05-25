"""Customer support agent preset with ticket handling and escalation tools."""

from __future__ import annotations

from typing import Any, Dict

from agentwork.core.agent import Agent
from agentwork.tools.decorators import tool


@tool(name="ticket_handler", description="Handle and resolve customer support tickets", retry_attempts=3)
def ticket_handler(ticket_id: str = "", issue: str = "") -> Dict[str, Any]:
    """Handle support tickets. Override with your ticket handling logic."""
    return {"ticket_id": ticket_id, "issue": issue, "status": "handled"}


@tool(name="faq_responder", description="Respond to frequently asked questions", retry_attempts=3)
def faq_responder(question: str = "", category: str = "general") -> Dict[str, Any]:
    """Respond to FAQs. Override with your FAQ logic."""
    return {"question": question, "category": category, "response": "answered"}


@tool(name="escalation_manager", description="Escalate complex issues to appropriate teams", retry_attempts=2)
def escalation_manager(ticket_id: str = "", severity: str = "medium") -> Dict[str, Any]:
    """Escalate issues. Override with your escalation logic."""
    return {"ticket_id": ticket_id, "severity": severity, "escalated": True}


def CustomerSupportAgent(name: str = "CustomerSupportAgent", **kwargs: Any) -> Agent:
    """Create a customer support agent pre-configured with support tools.

    Tools included:
    - ticket_handler: Handle and resolve customer support tickets
    - faq_responder: Respond to frequently asked questions
    - escalation_manager: Escalate complex issues to appropriate teams
    """
    return Agent(
        name=name,
        description="Customer support agent for ticket handling, FAQs, and escalation",
        tools=[ticket_handler, faq_responder, escalation_manager],
        capabilities=["support", "tickets", "customer_service", "escalation"],
        **kwargs,
    )
