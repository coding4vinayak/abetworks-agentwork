"""Marketing agent preset with content creation, campaigns, and analytics tools."""

from __future__ import annotations

from typing import Any, Dict, List

from agentwork.core.agent import Agent
from agentwork.tools.decorators import tool


@tool(name="content_creator", description="Create marketing content", retry_attempts=3)
def content_creator(
    topic: str = "", format: str = "blog", tone: str = "professional"
) -> Dict[str, Any]:
    """Create marketing content. Override with your content generation logic."""
    return {"topic": topic, "format": format, "tone": tone, "status": "created"}


@tool(name="campaign_manager", description="Manage marketing campaigns", retry_attempts=2)
def campaign_manager(
    action: str = "create", campaign_name: str = "", target_audience: str = ""
) -> Dict[str, Any]:
    """Manage marketing campaigns. Override with your campaign logic."""
    return {
        "action": action,
        "campaign": campaign_name,
        "audience": target_audience,
        "status": "active",
    }


@tool(name="analytics_tracker", description="Track and report marketing analytics", retry_attempts=2)
def analytics_tracker(
    metric: str = "impressions", period: str = "7d"
) -> Dict[str, Any]:
    """Track marketing analytics. Override with your analytics integration."""
    return {"metric": metric, "period": period, "value": 0, "status": "tracked"}


def MarketingAgent(name: str = "MarketingAgent", **kwargs: Any) -> Agent:
    """Create a marketing agent pre-configured with marketing tools.

    Tools included:
    - content_creator: Create marketing content (blogs, social posts, ads)
    - campaign_manager: Manage marketing campaigns
    - analytics_tracker: Track and report marketing analytics
    """
    return Agent(
        name=name,
        description="Marketing agent for content creation, campaign management, and analytics",
        tools=[content_creator, campaign_manager, analytics_tracker],
        capabilities=["content", "campaign", "analytics", "marketing"],
        **kwargs,
    )
