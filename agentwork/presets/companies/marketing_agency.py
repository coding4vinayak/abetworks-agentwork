"""Marketing agency company fleet preset with specialized agents for marketing workflows."""

from __future__ import annotations

from typing import Any, Dict, List

from agentwork.core.agent import Agent
from agentwork.tools.decorators import tool


# --- CampaignStrategist tools ---

@tool(name="campaign_planner", description="Plan and structure marketing campaigns", retry_attempts=2)
def campaign_planner(objective: str = "", budget: float = 0.0, duration: str = "30d") -> Dict[str, Any]:
    """Plan a marketing campaign."""
    return {"objective": objective, "budget": budget, "duration": duration, "status": "planned"}


@tool(name="audience_segmenter", description="Segment audiences for targeted marketing", retry_attempts=2)
def audience_segmenter(criteria: str = "", segment_size: int = 0) -> Dict[str, Any]:
    """Segment an audience based on criteria."""
    return {"criteria": criteria, "segment_size": segment_size, "segments": [], "status": "segmented"}


@tool(name="budget_allocator", description="Allocate marketing budget across channels", retry_attempts=2)
def budget_allocator(total_budget: float = 0.0, channels: List[str] = None) -> Dict[str, Any]:
    """Allocate budget across marketing channels."""
    return {"total_budget": total_budget, "channels": channels or [], "allocations": {}, "status": "allocated"}


# --- SocialMediaManager tools ---

@tool(name="post_scheduler", description="Schedule social media posts across platforms", retry_attempts=2)
def post_scheduler(content: str = "", platform: str = "", scheduled_time: str = "") -> Dict[str, Any]:
    """Schedule a social media post."""
    return {"content": content, "platform": platform, "scheduled_time": scheduled_time, "status": "scheduled"}


@tool(name="engagement_tracker", description="Track social media engagement metrics", retry_attempts=2)
def engagement_tracker(platform: str = "", post_id: str = "") -> Dict[str, Any]:
    """Track engagement for a post."""
    return {"platform": platform, "post_id": post_id, "likes": 0, "shares": 0, "status": "tracked"}


@tool(name="hashtag_optimizer", description="Optimize hashtags for reach and engagement", retry_attempts=2)
def hashtag_optimizer(topic: str = "", count: int = 5) -> Dict[str, Any]:
    """Optimize hashtags for a topic."""
    return {"topic": topic, "count": count, "hashtags": [], "status": "optimized"}


# --- SEOSpecialist tools ---

@tool(name="keyword_researcher", description="Research keywords for SEO optimization", retry_attempts=2)
def keyword_researcher(topic: str = "", region: str = "global") -> Dict[str, Any]:
    """Research keywords for a topic."""
    return {"topic": topic, "region": region, "keywords": [], "status": "researched"}


@tool(name="backlink_analyzer", description="Analyze backlink profiles and opportunities", retry_attempts=2)
def backlink_analyzer(url: str = "", competitor_url: str = "") -> Dict[str, Any]:
    """Analyze backlinks for a URL."""
    return {"url": url, "competitor_url": competitor_url, "backlinks": 0, "status": "analyzed"}


@tool(name="rank_tracker", description="Track search engine rankings for keywords", retry_attempts=2)
def rank_tracker(keywords: List[str] = None, domain: str = "") -> Dict[str, Any]:
    """Track rankings for keywords."""
    return {"keywords": keywords or [], "domain": domain, "rankings": {}, "status": "tracked"}


# --- ContentProducer tools ---

@tool(name="blog_writer", description="Write blog posts and articles", retry_attempts=2)
def blog_writer(topic: str = "", word_count: int = 500, tone: str = "professional") -> Dict[str, Any]:
    """Write a blog post."""
    return {"topic": topic, "word_count": word_count, "tone": tone, "content": "", "status": "written"}


@tool(name="video_scripter", description="Write video scripts and outlines", retry_attempts=2)
def video_scripter(topic: str = "", duration: str = "5min") -> Dict[str, Any]:
    """Write a video script."""
    return {"topic": topic, "duration": duration, "script": "", "status": "scripted"}


@tool(name="infographic_designer", description="Design infographic layouts and content", retry_attempts=2)
def infographic_designer(topic: str = "", data_points: int = 5) -> Dict[str, Any]:
    """Design an infographic."""
    return {"topic": topic, "data_points": data_points, "layout": "", "status": "designed"}


# --- AdBuyer tools ---

@tool(name="ad_placement", description="Place ads across advertising platforms", retry_attempts=3)
def ad_placement(platform: str = "", ad_type: str = "display", budget: float = 0.0) -> Dict[str, Any]:
    """Place an ad on a platform."""
    return {"platform": platform, "ad_type": ad_type, "budget": budget, "status": "placed"}


@tool(name="bid_optimizer", description="Optimize ad bidding strategies", retry_attempts=2)
def bid_optimizer(campaign_id: str = "", target_cpa: float = 0.0) -> Dict[str, Any]:
    """Optimize bids for a campaign."""
    return {"campaign_id": campaign_id, "target_cpa": target_cpa, "optimized_bid": 0.0, "status": "optimized"}


@tool(name="roi_calculator", description="Calculate return on investment for campaigns", retry_attempts=2)
def roi_calculator(spend: float = 0.0, revenue: float = 0.0) -> Dict[str, Any]:
    """Calculate ROI for a campaign."""
    roi = ((revenue - spend) / spend * 100) if spend > 0 else 0.0
    return {"spend": spend, "revenue": revenue, "roi_percent": roi, "status": "calculated"}


def MarketingAgencyCompany(prefix: str = "MarketingAgency") -> List[Agent]:
    """Create a marketing agency fleet with specialized agents.

    Returns a list of agents:
    - CampaignStrategist: campaign planning, audience segmentation, budget allocation
    - SocialMediaManager: post scheduling, engagement tracking, hashtag optimization
    - SEOSpecialist: keyword research, backlink analysis, rank tracking
    - ContentProducer: blog writing, video scripting, infographic design
    - AdBuyer: ad placement, bid optimization, ROI calculation
    """
    return [
        Agent(
            name=f"{prefix}_CampaignStrategist",
            description="Campaign strategist agent for planning and audience targeting",
            tools=[campaign_planner, audience_segmenter, budget_allocator],
            capabilities=["campaigns", "strategy", "audience", "budget"],
        ),
        Agent(
            name=f"{prefix}_SocialMediaManager",
            description="Social media manager agent for posting and engagement",
            tools=[post_scheduler, engagement_tracker, hashtag_optimizer],
            capabilities=["social_media", "engagement", "scheduling", "hashtags"],
        ),
        Agent(
            name=f"{prefix}_SEOSpecialist",
            description="SEO specialist agent for search optimization",
            tools=[keyword_researcher, backlink_analyzer, rank_tracker],
            capabilities=["seo", "keywords", "backlinks", "rankings"],
        ),
        Agent(
            name=f"{prefix}_ContentProducer",
            description="Content producer agent for blogs, videos, and infographics",
            tools=[blog_writer, video_scripter, infographic_designer],
            capabilities=["content", "writing", "video", "design"],
        ),
        Agent(
            name=f"{prefix}_AdBuyer",
            description="Ad buyer agent for ad placement and optimization",
            tools=[ad_placement, bid_optimizer, roi_calculator],
            capabilities=["advertising", "ads", "bidding", "roi"],
        ),
    ]
