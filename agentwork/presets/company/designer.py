"""Designer agent preset with UI design and branding tools."""

from __future__ import annotations

from typing import Any, Dict

from agentwork.core.agent import Agent
from agentwork.tools.decorators import tool


@tool(name="ui_designer", description="Design user interfaces and layouts", retry_attempts=3)
def ui_designer(page: str = "", style: str = "modern") -> Dict[str, Any]:
    """Design UI layouts. Override with your UI design logic."""
    return {"page": page, "style": style, "design": "completed", "components": 0}


@tool(name="mockup_creator", description="Create visual mockups and wireframes", retry_attempts=3)
def mockup_creator(concept: str = "", fidelity: str = "high") -> Dict[str, Any]:
    """Create mockups. Override with your mockup creation logic."""
    return {"concept": concept, "fidelity": fidelity, "mockup": "created"}


@tool(name="brand_styler", description="Define and apply brand styling guidelines", retry_attempts=2)
def brand_styler(brand: str = "", element: str = "colors") -> Dict[str, Any]:
    """Apply brand styling. Override with your brand styling logic."""
    return {"brand": brand, "element": element, "style_applied": True}


def DesignerAgent(name: str = "DesignerAgent", **kwargs: Any) -> Agent:
    """Create a designer agent pre-configured with design and branding tools.

    Tools included:
    - ui_designer: Design user interfaces and layouts
    - mockup_creator: Create visual mockups and wireframes
    - brand_styler: Define and apply brand styling guidelines
    """
    return Agent(
        name=name,
        description="Design agent for UI design, mockups, and brand styling",
        tools=[ui_designer, mockup_creator, brand_styler],
        capabilities=["design", "ui", "branding", "creative"],
        **kwargs,
    )
