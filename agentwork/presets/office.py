"""Office agent preset with document processing, email, and data entry tools."""

from __future__ import annotations

from typing import Any, Dict

from agentwork.core.agent import Agent
from agentwork.tools.decorators import tool


@tool(name="document_processor", description="Process and transform documents", retry_attempts=3)
def document_processor(content: str = "", format: str = "text") -> Dict[str, Any]:
    """Process a document. Override this with your actual document processing logic."""
    return {"processed": True, "content": content, "format": format}


@tool(name="email_handler", description="Send and manage emails", retry_attempts=3)
def email_handler(
    to: str = "", subject: str = "", body: str = "", action: str = "send"
) -> Dict[str, Any]:
    """Handle email operations. Override with your email integration."""
    return {"action": action, "to": to, "subject": subject, "status": "queued"}


@tool(name="data_entry", description="Automated data entry and form filling", retry_attempts=2)
def data_entry(data: Dict[str, Any] = None, target: str = "") -> Dict[str, Any]:
    """Perform data entry operations. Override with your data entry logic."""
    return {"entered": True, "target": target, "fields": len(data or {})}


@tool(name="spreadsheet_manager", description="Manage spreadsheets and tabular data", retry_attempts=2)
def spreadsheet_manager(
    operation: str = "read", sheet: str = "", data: Any = None
) -> Dict[str, Any]:
    """Manage spreadsheet operations. Override with your spreadsheet logic."""
    return {"operation": operation, "sheet": sheet, "status": "completed"}


def OfficeAgent(name: str = "OfficeAgent", **kwargs: Any) -> Agent:
    """Create an office agent pre-configured with office productivity tools.

    Tools included:
    - document_processor: Process and transform documents
    - email_handler: Send and manage emails
    - data_entry: Automated data entry and form filling
    - spreadsheet_manager: Manage spreadsheets and tabular data

    You can override any tool by removing it and adding your own.
    """
    return Agent(
        name=name,
        description="Office productivity agent for document processing, email, and data entry",
        tools=[document_processor, email_handler, data_entry, spreadsheet_manager],
        capabilities=["document", "email", "data_entry", "spreadsheet", "office"],
        **kwargs,
    )
