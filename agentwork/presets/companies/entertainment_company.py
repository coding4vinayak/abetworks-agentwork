"""Entertainment company fleet preset with specialized agents for media workflows."""

from __future__ import annotations

from typing import Any, Dict, List

from agentwork.core.agent import Agent
from agentwork.tools.decorators import tool


# --- ContentProducer tools ---

@tool(name="script_writer", description="Write scripts for shows and content", retry_attempts=2)
def script_writer(title: str = "", genre: str = "", episode: int = 1) -> Dict[str, Any]:
    """Write a script for content."""
    return {"title": title, "genre": genre, "episode": episode, "pages": 0, "status": "written"}


@tool(name="scene_planner", description="Plan scenes and production schedules", retry_attempts=2)
def scene_planner(project: str = "", scene_count: int = 0, location: str = "") -> Dict[str, Any]:
    """Plan scenes for a production."""
    return {"project": project, "scene_count": scene_count, "location": location, "status": "planned"}


@tool(name="talent_coordinator", description="Coordinate talent and casting", retry_attempts=2)
def talent_coordinator(role: str = "", requirements: str = "") -> Dict[str, Any]:
    """Coordinate talent for a role."""
    return {"role": role, "requirements": requirements, "candidates": [], "status": "coordinated"}


# --- Scheduler tools ---

@tool(name="release_planner", description="Plan content release schedules", retry_attempts=2)
def release_planner(content_id: str = "", release_date: str = "", platform: str = "") -> Dict[str, Any]:
    """Plan a content release."""
    return {"content_id": content_id, "release_date": release_date, "platform": platform, "status": "planned"}


@tool(name="event_coordinator", description="Coordinate events and premieres", retry_attempts=2)
def event_coordinator(event_name: str = "", venue: str = "", date: str = "") -> Dict[str, Any]:
    """Coordinate an event."""
    return {"event_name": event_name, "venue": venue, "date": date, "status": "coordinated"}


@tool(name="calendar_manager", description="Manage production calendars and timelines", retry_attempts=2)
def calendar_manager(project: str = "", start_date: str = "", end_date: str = "") -> Dict[str, Any]:
    """Manage a production calendar."""
    return {"project": project, "start_date": start_date, "end_date": end_date, "status": "managed"}


# --- Distributor tools ---

@tool(name="platform_publisher", description="Publish content to distribution platforms", retry_attempts=3)
def platform_publisher(content_id: str = "", platform: str = "", region: str = "global") -> Dict[str, Any]:
    """Publish content to a platform."""
    return {"content_id": content_id, "platform": platform, "region": region, "status": "published"}


@tool(name="syndication_manager", description="Manage content syndication and licensing", retry_attempts=2)
def syndication_manager(content_id: str = "", partner: str = "", terms: str = "") -> Dict[str, Any]:
    """Manage syndication for content."""
    return {"content_id": content_id, "partner": partner, "terms": terms, "status": "syndicated"}


@tool(name="rights_tracker", description="Track content rights and royalties", retry_attempts=2)
def rights_tracker(content_id: str = "", territory: str = "worldwide") -> Dict[str, Any]:
    """Track rights for content."""
    return {"content_id": content_id, "territory": territory, "rights": [], "status": "tracked"}


# --- AudienceManager tools ---

@tool(name="fan_engagement", description="Manage fan engagement and interactions", retry_attempts=2)
def fan_engagement(campaign: str = "", platform: str = "") -> Dict[str, Any]:
    """Manage fan engagement."""
    return {"campaign": campaign, "platform": platform, "engagement_rate": 0.0, "status": "engaged"}


@tool(name="feedback_collector", description="Collect and analyze audience feedback", retry_attempts=2)
def feedback_collector(content_id: str = "", source: str = "") -> Dict[str, Any]:
    """Collect audience feedback."""
    return {"content_id": content_id, "source": source, "feedback": [], "sentiment": "neutral", "status": "collected"}


@tool(name="community_moderator", description="Moderate community discussions and forums", retry_attempts=2)
def community_moderator(community: str = "", action: str = "review") -> Dict[str, Any]:
    """Moderate a community."""
    return {"community": community, "action": action, "issues": 0, "status": "moderated"}


def EntertainmentCompany(prefix: str = "Entertainment") -> List[Agent]:
    """Create an entertainment company fleet with specialized agents.

    Returns a list of agents:
    - ContentProducer: script writing, scene planning, talent coordination
    - Scheduler: release planning, event coordination, calendar management
    - Distributor: platform publishing, syndication, rights tracking
    - AudienceManager: fan engagement, feedback collection, community moderation
    """
    return [
        Agent(
            name=f"{prefix}_ContentProducer",
            description="Content producer agent for scripts, scenes, and talent",
            tools=[script_writer, scene_planner, talent_coordinator],
            capabilities=["content_production", "scripts", "talent", "production"],
        ),
        Agent(
            name=f"{prefix}_Scheduler",
            description="Scheduler agent for releases, events, and calendars",
            tools=[release_planner, event_coordinator, calendar_manager],
            capabilities=["scheduling", "releases", "events", "calendar"],
        ),
        Agent(
            name=f"{prefix}_Distributor",
            description="Distributor agent for publishing, syndication, and rights",
            tools=[platform_publisher, syndication_manager, rights_tracker],
            capabilities=["distribution", "publishing", "syndication", "rights"],
        ),
        Agent(
            name=f"{prefix}_AudienceManager",
            description="Audience manager agent for fans, feedback, and community",
            tools=[fan_engagement, feedback_collector, community_moderator],
            capabilities=["audience", "fans", "feedback", "community"],
        ),
    ]
