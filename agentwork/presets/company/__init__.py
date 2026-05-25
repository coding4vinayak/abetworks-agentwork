"""Company role-based agent presets for organizational workflows."""

from agentwork.presets.company.ceo import CEOAgent
from agentwork.presets.company.cto import CTOAgent
from agentwork.presets.company.developer import DeveloperAgent
from agentwork.presets.company.designer import DesignerAgent
from agentwork.presets.company.content_writer import ContentWriterAgent
from agentwork.presets.company.hr import HRAgent
from agentwork.presets.company.finance import FinanceAgent
from agentwork.presets.company.support import CustomerSupportAgent
from agentwork.presets.company.project_manager import ProjectManagerAgent

__all__ = [
    "CEOAgent",
    "CTOAgent",
    "DeveloperAgent",
    "DesignerAgent",
    "ContentWriterAgent",
    "HRAgent",
    "FinanceAgent",
    "CustomerSupportAgent",
    "ProjectManagerAgent",
]
