"""Digital agent preset with web scraping, SEO, and social media tools."""

from __future__ import annotations

from typing import Any, Dict, List

from agentwork.core.agent import Agent
from agentwork.tools.decorators import tool


@tool(name="web_scraper", description="Scrape and extract data from web pages", retry_attempts=3)
def web_scraper(url: str = "", selectors: List[str] = None) -> Dict[str, Any]:
    """Scrape web pages. Override with your scraping logic."""
    return {"url": url, "selectors": selectors or [], "data": {}, "status": "scraped"}


@tool(name="seo_optimizer", description="Analyze and optimize SEO", retry_attempts=2)
def seo_optimizer(
    url: str = "", keywords: List[str] = None, action: str = "analyze"
) -> Dict[str, Any]:
    """Optimize SEO. Override with your SEO logic."""
    return {"url": url, "keywords": keywords or [], "action": action, "score": 0, "status": "analyzed"}


@tool(name="social_media_poster", description="Post and manage social media content", retry_attempts=3)
def social_media_poster(
    platform: str = "twitter", content: str = "", action: str = "post"
) -> Dict[str, Any]:
    """Manage social media. Override with your social media integration."""
    return {"platform": platform, "action": action, "content_length": len(content), "status": "posted"}


def DigitalAgent(name: str = "DigitalAgent", **kwargs: Any) -> Agent:
    """Create a digital agent pre-configured with digital marketing tools.

    Tools included:
    - web_scraper: Scrape and extract data from web pages
    - seo_optimizer: Analyze and optimize SEO
    - social_media_poster: Post and manage social media content
    """
    return Agent(
        name=name,
        description="Digital agent for web scraping, SEO optimization, and social media",
        tools=[web_scraper, seo_optimizer, social_media_poster],
        capabilities=["web_scraping", "seo", "social_media", "digital"],
        **kwargs,
    )
