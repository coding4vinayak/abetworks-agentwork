"""Entertainment agent preset with content curation and recommendation tools."""

from __future__ import annotations

from typing import Any, Dict, List

from agentwork.core.agent import Agent
from agentwork.tools.decorators import tool


@tool(name="content_curator", description="Curate and organize entertainment content", retry_attempts=2)
def content_curator(
    category: str = "general", tags: List[str] = None, limit: int = 10
) -> Dict[str, Any]:
    """Curate content. Override with your curation logic."""
    return {"category": category, "tags": tags or [], "limit": limit, "items": [], "status": "curated"}


@tool(name="recommendation_engine", description="Generate personalized recommendations", retry_attempts=2)
def recommendation_engine(
    user_id: str = "", preferences: Dict[str, Any] = None, count: int = 5
) -> Dict[str, Any]:
    """Generate recommendations. Override with your recommendation logic."""
    return {
        "user_id": user_id,
        "preferences": preferences or {},
        "count": count,
        "recommendations": [],
        "status": "generated",
    }


def EntertainmentAgent(name: str = "EntertainmentAgent", **kwargs: Any) -> Agent:
    """Create an entertainment agent pre-configured with content tools.

    Tools included:
    - content_curator: Curate and organize entertainment content
    - recommendation_engine: Generate personalized recommendations
    """
    return Agent(
        name=name,
        description="Entertainment agent for content curation and recommendations",
        tools=[content_curator, recommendation_engine],
        capabilities=["content_curation", "recommendations", "entertainment"],
        **kwargs,
    )
