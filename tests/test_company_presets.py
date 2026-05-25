"""Tests for company role-based agent presets."""

from __future__ import annotations

import pytest

from agentwork.presets.company import (
    CEOAgent,
    CTOAgent,
    DeveloperAgent,
    DesignerAgent,
    ContentWriterAgent,
    HRAgent,
    FinanceAgent,
    CustomerSupportAgent,
    ProjectManagerAgent,
)


class TestCEOAgent:
    def test_instantiation(self):
        agent = CEOAgent()
        assert agent.name == "CEOAgent"
        assert "strategy" in agent.capabilities
        assert "delegation" in agent.capabilities
        assert "leadership" in agent.capabilities
        assert "ceo" in agent.capabilities

    def test_tools(self):
        agent = CEOAgent()
        assert "strategic_planning" in agent.tool_names
        assert "decision_maker" in agent.tool_names
        assert "task_delegator" in agent.tool_names

    def test_execute_tool(self):
        agent = CEOAgent()
        result = agent.execute("strategic_planning", {"goal": "growth", "timeline": "yearly"})
        assert result.success
        assert result.output["plan"] == "growth"

    def test_custom_name(self):
        agent = CEOAgent(name="MyCEO")
        assert agent.name == "MyCEO"


class TestCTOAgent:
    def test_instantiation(self):
        agent = CTOAgent()
        assert agent.name == "CTOAgent"
        assert "architecture" in agent.capabilities
        assert "technology" in agent.capabilities
        assert "code_review" in agent.capabilities
        assert "cto" in agent.capabilities

    def test_tools(self):
        agent = CTOAgent()
        assert "architecture_designer" in agent.tool_names
        assert "tech_stack_evaluator" in agent.tool_names
        assert "code_reviewer" in agent.tool_names

    def test_execute_tool(self):
        agent = CTOAgent()
        result = agent.execute("architecture_designer", {"system": "api", "requirements": {"scale": "high"}})
        assert result.success
        assert result.output["system"] == "api"


class TestDeveloperAgent:
    def test_instantiation(self):
        agent = DeveloperAgent()
        assert agent.name == "DeveloperAgent"
        assert "coding" in agent.capabilities
        assert "testing" in agent.capabilities
        assert "debugging" in agent.capabilities
        assert "development" in agent.capabilities

    def test_tools(self):
        agent = DeveloperAgent()
        assert "code_generator" in agent.tool_names
        assert "bug_fixer" in agent.tool_names
        assert "test_writer" in agent.tool_names
        assert "code_refactorer" in agent.tool_names

    def test_execute_tool(self):
        agent = DeveloperAgent()
        result = agent.execute("code_generator", {"spec": "hello world", "language": "python"})
        assert result.success
        assert result.output["language"] == "python"


class TestDesignerAgent:
    def test_instantiation(self):
        agent = DesignerAgent()
        assert agent.name == "DesignerAgent"
        assert "design" in agent.capabilities
        assert "ui" in agent.capabilities
        assert "branding" in agent.capabilities
        assert "creative" in agent.capabilities

    def test_tools(self):
        agent = DesignerAgent()
        assert "ui_designer" in agent.tool_names
        assert "mockup_creator" in agent.tool_names
        assert "brand_styler" in agent.tool_names

    def test_execute_tool(self):
        agent = DesignerAgent()
        result = agent.execute("ui_designer", {"page": "home", "style": "minimal"})
        assert result.success
        assert result.output["page"] == "home"


class TestContentWriterAgent:
    def test_instantiation(self):
        agent = ContentWriterAgent()
        assert agent.name == "ContentWriterAgent"
        assert "writing" in agent.capabilities
        assert "content" in agent.capabilities
        assert "copywriting" in agent.capabilities
        assert "documentation" in agent.capabilities

    def test_tools(self):
        agent = ContentWriterAgent()
        assert "article_writer" in agent.tool_names
        assert "copywriter" in agent.tool_names
        assert "technical_writer" in agent.tool_names

    def test_execute_tool(self):
        agent = ContentWriterAgent()
        result = agent.execute("article_writer", {"topic": "AI", "tone": "casual"})
        assert result.success
        assert result.output["topic"] == "AI"


class TestHRAgent:
    def test_instantiation(self):
        agent = HRAgent()
        assert agent.name == "HRAgent"
        assert "hiring" in agent.capabilities
        assert "onboarding" in agent.capabilities
        assert "hr" in agent.capabilities
        assert "performance" in agent.capabilities

    def test_tools(self):
        agent = HRAgent()
        assert "recruiter" in agent.tool_names
        assert "onboarding_manager" in agent.tool_names
        assert "performance_reviewer" in agent.tool_names

    def test_execute_tool(self):
        agent = HRAgent()
        result = agent.execute("recruiter", {"position": "engineer", "requirements": {"level": "senior"}})
        assert result.success
        assert result.output["position"] == "engineer"


class TestFinanceAgent:
    def test_instantiation(self):
        agent = FinanceAgent()
        assert agent.name == "FinanceAgent"
        assert "budget" in agent.capabilities
        assert "invoicing" in agent.capabilities
        assert "finance" in agent.capabilities
        assert "reporting" in agent.capabilities

    def test_tools(self):
        agent = FinanceAgent()
        assert "budget_planner" in agent.tool_names
        assert "invoice_processor" in agent.tool_names
        assert "financial_reporter" in agent.tool_names

    def test_execute_tool(self):
        agent = FinanceAgent()
        result = agent.execute("budget_planner", {"department": "engineering", "period": "yearly"})
        assert result.success
        assert result.output["department"] == "engineering"


class TestCustomerSupportAgent:
    def test_instantiation(self):
        agent = CustomerSupportAgent()
        assert agent.name == "CustomerSupportAgent"
        assert "support" in agent.capabilities
        assert "tickets" in agent.capabilities
        assert "customer_service" in agent.capabilities
        assert "escalation" in agent.capabilities

    def test_tools(self):
        agent = CustomerSupportAgent()
        assert "ticket_handler" in agent.tool_names
        assert "faq_responder" in agent.tool_names
        assert "escalation_manager" in agent.tool_names

    def test_execute_tool(self):
        agent = CustomerSupportAgent()
        result = agent.execute("ticket_handler", {"ticket_id": "T-123", "issue": "login problem"})
        assert result.success
        assert result.output["ticket_id"] == "T-123"


class TestProjectManagerAgent:
    def test_instantiation(self):
        agent = ProjectManagerAgent()
        assert agent.name == "ProjectManagerAgent"
        assert "project_management" in agent.capabilities
        assert "planning" in agent.capabilities
        assert "tracking" in agent.capabilities
        assert "status" in agent.capabilities

    def test_tools(self):
        agent = ProjectManagerAgent()
        assert "task_tracker" in agent.tool_names
        assert "timeline_planner" in agent.tool_names
        assert "status_reporter" in agent.tool_names

    def test_execute_tool(self):
        agent = ProjectManagerAgent()
        result = agent.execute("task_tracker", {"task": "deploy v2", "status": "in_progress"})
        assert result.success
        assert result.output["task"] == "deploy v2"
