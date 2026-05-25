"""Digital agency company fleet preset with specialized agents for software development."""

from __future__ import annotations

from typing import Any, Dict, List

from agentwork.core.agent import Agent
from agentwork.tools.decorators import tool


# --- FrontendDev tools ---

@tool(name="ui_builder", description="Build user interface components", retry_attempts=2)
def ui_builder(component: str = "", framework: str = "react", style: str = "") -> Dict[str, Any]:
    """Build a UI component."""
    return {"component": component, "framework": framework, "style": style, "status": "built"}


@tool(name="responsive_tester", description="Test responsive design across devices", retry_attempts=2)
def responsive_tester(url: str = "", devices: List[str] = None) -> Dict[str, Any]:
    """Test responsive design."""
    return {"url": url, "devices": devices or [], "issues": [], "status": "tested"}


@tool(name="accessibility_checker", description="Check accessibility compliance", retry_attempts=2)
def accessibility_checker(url: str = "", standard: str = "WCAG2.1") -> Dict[str, Any]:
    """Check accessibility compliance."""
    return {"url": url, "standard": standard, "violations": [], "score": 100, "status": "checked"}


# --- BackendDev tools ---

@tool(name="api_builder", description="Build and configure API endpoints", retry_attempts=2)
def api_builder(endpoint: str = "", method: str = "GET", schema: str = "") -> Dict[str, Any]:
    """Build an API endpoint."""
    return {"endpoint": endpoint, "method": method, "schema": schema, "status": "built"}


@tool(name="database_designer", description="Design database schemas and migrations", retry_attempts=2)
def database_designer(table_name: str = "", columns: List[str] = None) -> Dict[str, Any]:
    """Design a database schema."""
    return {"table_name": table_name, "columns": columns or [], "migration": "", "status": "designed"}


@tool(name="auth_implementer", description="Implement authentication and authorization", retry_attempts=3)
def auth_implementer(auth_type: str = "jwt", provider: str = "") -> Dict[str, Any]:
    """Implement authentication."""
    return {"auth_type": auth_type, "provider": provider, "status": "implemented"}


# --- QAEngineer tools ---

@tool(name="test_runner", description="Run automated test suites", retry_attempts=2)
def test_runner(test_suite: str = "", coverage: bool = True) -> Dict[str, Any]:
    """Run a test suite."""
    return {"test_suite": test_suite, "coverage": coverage, "passed": 0, "failed": 0, "status": "completed"}


@tool(name="bug_reporter", description="Report and track bugs", retry_attempts=2)
def bug_reporter(title: str = "", severity: str = "medium", steps: str = "") -> Dict[str, Any]:
    """Report a bug."""
    return {"title": title, "severity": severity, "steps": steps, "bug_id": "", "status": "reported"}


@tool(name="load_tester", description="Run load and performance tests", retry_attempts=3)
def load_tester(url: str = "", concurrent_users: int = 100, duration: str = "60s") -> Dict[str, Any]:
    """Run a load test."""
    return {"url": url, "concurrent_users": concurrent_users, "duration": duration, "avg_response_ms": 0, "status": "completed"}


# --- DevOpsEngineer tools ---

@tool(name="deployer", description="Deploy applications to environments", retry_attempts=3)
def deployer(app_name: str = "", environment: str = "staging", version: str = "") -> Dict[str, Any]:
    """Deploy an application."""
    return {"app_name": app_name, "environment": environment, "version": version, "status": "deployed"}


@tool(name="monitor_setup", description="Set up monitoring and alerting", retry_attempts=2)
def monitor_setup(service: str = "", metrics: List[str] = None, threshold: float = 0.0) -> Dict[str, Any]:
    """Set up monitoring for a service."""
    return {"service": service, "metrics": metrics or [], "threshold": threshold, "status": "configured"}


@tool(name="log_analyzer", description="Analyze application logs for issues", retry_attempts=2)
def log_analyzer(service: str = "", time_range: str = "1h", level: str = "error") -> Dict[str, Any]:
    """Analyze logs for a service."""
    return {"service": service, "time_range": time_range, "level": level, "entries": [], "status": "analyzed"}


# --- UXDesigner tools ---

@tool(name="wireframe_creator", description="Create wireframes for UI designs", retry_attempts=2)
def wireframe_creator(page_name: str = "", layout: str = "single-column") -> Dict[str, Any]:
    """Create a wireframe."""
    return {"page_name": page_name, "layout": layout, "elements": [], "status": "created"}


@tool(name="prototype_builder", description="Build interactive prototypes", retry_attempts=2)
def prototype_builder(project: str = "", pages: List[str] = None) -> Dict[str, Any]:
    """Build a prototype."""
    return {"project": project, "pages": pages or [], "prototype_url": "", "status": "built"}


@tool(name="usability_tester", description="Run usability tests and collect feedback", retry_attempts=2)
def usability_tester(prototype_id: str = "", participants: int = 5) -> Dict[str, Any]:
    """Run usability tests."""
    return {"prototype_id": prototype_id, "participants": participants, "feedback": [], "score": 0.0, "status": "tested"}


def DigitalAgencyCompany(prefix: str = "DigitalAgency") -> List[Agent]:
    """Create a digital agency fleet with specialized agents.

    Returns a list of agents:
    - FrontendDev: UI building, responsive testing, accessibility checking
    - BackendDev: API building, database design, auth implementation
    - QAEngineer: test running, bug reporting, load testing
    - DevOpsEngineer: deployment, monitoring, log analysis
    - UXDesigner: wireframes, prototypes, usability testing
    """
    return [
        Agent(
            name=f"{prefix}_FrontendDev",
            description="Frontend developer agent for UI and responsive design",
            tools=[ui_builder, responsive_tester, accessibility_checker],
            capabilities=["frontend", "ui", "responsive", "accessibility"],
        ),
        Agent(
            name=f"{prefix}_BackendDev",
            description="Backend developer agent for APIs, databases, and auth",
            tools=[api_builder, database_designer, auth_implementer],
            capabilities=["backend", "api", "database", "auth"],
        ),
        Agent(
            name=f"{prefix}_QAEngineer",
            description="QA engineer agent for testing and bug reporting",
            tools=[test_runner, bug_reporter, load_tester],
            capabilities=["qa", "testing", "bugs", "performance"],
        ),
        Agent(
            name=f"{prefix}_DevOpsEngineer",
            description="DevOps engineer agent for deployment and monitoring",
            tools=[deployer, monitor_setup, log_analyzer],
            capabilities=["devops", "deployment", "monitoring", "logs"],
        ),
        Agent(
            name=f"{prefix}_UXDesigner",
            description="UX designer agent for wireframes and usability",
            tools=[wireframe_creator, prototype_builder, usability_tester],
            capabilities=["ux", "design", "wireframes", "prototypes"],
        ),
    ]
