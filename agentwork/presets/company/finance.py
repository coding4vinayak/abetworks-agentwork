"""Finance agent preset with budgeting and financial reporting tools."""

from __future__ import annotations

from typing import Any, Dict

from agentwork.core.agent import Agent
from agentwork.tools.decorators import tool


@tool(name="budget_planner", description="Plan and manage budgets", retry_attempts=3)
def budget_planner(department: str = "", period: str = "quarterly") -> Dict[str, Any]:
    """Plan budgets. Override with your budget planning logic."""
    return {"department": department, "period": period, "budget": "planned"}


@tool(name="invoice_processor", description="Process and manage invoices", retry_attempts=3)
def invoice_processor(invoice_id: str = "", amount: float = 0.0) -> Dict[str, Any]:
    """Process invoices. Override with your invoice processing logic."""
    return {"invoice_id": invoice_id, "amount": amount, "status": "processed"}


@tool(name="financial_reporter", description="Generate financial reports and summaries", retry_attempts=2)
def financial_reporter(report_type: str = "summary", period: str = "monthly") -> Dict[str, Any]:
    """Generate financial reports. Override with your reporting logic."""
    return {"report_type": report_type, "period": period, "report": "generated"}


def FinanceAgent(name: str = "FinanceAgent", **kwargs: Any) -> Agent:
    """Create a finance agent pre-configured with financial management tools.

    Tools included:
    - budget_planner: Plan and manage budgets
    - invoice_processor: Process and manage invoices
    - financial_reporter: Generate financial reports and summaries
    """
    return Agent(
        name=name,
        description="Finance agent for budgeting, invoicing, and financial reporting",
        tools=[budget_planner, invoice_processor, financial_reporter],
        capabilities=["budget", "invoicing", "finance", "reporting"],
        **kwargs,
    )
