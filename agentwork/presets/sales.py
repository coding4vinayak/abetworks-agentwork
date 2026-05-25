"""Sales agent preset with lead generation, outreach, and CRM tools."""

from __future__ import annotations

from typing import Any, Dict

from agentwork.core.agent import Agent
from agentwork.tools.decorators import tool


@tool(name="lead_generator", description="Generate and qualify leads", retry_attempts=3)
def lead_generator(
    source: str = "web", criteria: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Generate leads. Override with your lead generation logic."""
    return {"source": source, "criteria": criteria or {}, "leads_found": 0, "status": "searched"}


@tool(name="outreach_manager", description="Manage sales outreach campaigns", retry_attempts=3)
def outreach_manager(
    action: str = "send", template: str = "", recipients: int = 0
) -> Dict[str, Any]:
    """Manage outreach. Override with your outreach logic."""
    return {"action": action, "template": template, "recipients": recipients, "status": "queued"}


@tool(name="crm_updater", description="Update CRM records", retry_attempts=2)
def crm_updater(
    entity: str = "contact", entity_id: str = "", data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Update CRM. Override with your CRM integration."""
    return {"entity": entity, "id": entity_id, "updated_fields": len(data or {}), "status": "updated"}


def SalesAgent(name: str = "SalesAgent", **kwargs: Any) -> Agent:
    """Create a sales agent pre-configured with sales tools.

    Tools included:
    - lead_generator: Generate and qualify leads
    - outreach_manager: Manage sales outreach campaigns
    - crm_updater: Update CRM records
    """
    return Agent(
        name=name,
        description="Sales agent for lead generation, outreach, and CRM management",
        tools=[lead_generator, outreach_manager, crm_updater],
        capabilities=["leads", "outreach", "crm", "sales"],
        **kwargs,
    )
