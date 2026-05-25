"""Content writer agent preset with writing and documentation tools."""

from __future__ import annotations

from typing import Any, Dict

from agentwork.core.agent import Agent
from agentwork.tools.decorators import tool


@tool(name="article_writer", description="Write articles and blog posts", retry_attempts=3)
def article_writer(topic: str = "", tone: str = "professional") -> Dict[str, Any]:
    """Write articles. Override with your article writing logic."""
    return {"topic": topic, "tone": tone, "article": "drafted", "word_count": 0}


@tool(name="copywriter", description="Write marketing copy and advertisements", retry_attempts=3)
def copywriter(product: str = "", audience: str = "general") -> Dict[str, Any]:
    """Write marketing copy. Override with your copywriting logic."""
    return {"product": product, "audience": audience, "copy": "written"}


@tool(name="technical_writer", description="Write technical documentation and guides", retry_attempts=2)
def technical_writer(subject: str = "", format: str = "markdown") -> Dict[str, Any]:
    """Write technical docs. Override with your technical writing logic."""
    return {"subject": subject, "format": format, "documentation": "created"}


def ContentWriterAgent(name: str = "ContentWriterAgent", **kwargs: Any) -> Agent:
    """Create a content writer agent pre-configured with writing tools.

    Tools included:
    - article_writer: Write articles and blog posts
    - copywriter: Write marketing copy and advertisements
    - technical_writer: Write technical documentation and guides
    """
    return Agent(
        name=name,
        description="Content creation agent for articles, copy, and technical documentation",
        tools=[article_writer, copywriter, technical_writer],
        capabilities=["writing", "content", "copywriting", "documentation"],
        **kwargs,
    )
