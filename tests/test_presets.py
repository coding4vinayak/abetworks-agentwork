"""Tests for domain-specific agent presets."""

import pytest

from agentwork.presets import (
    OfficeAgent,
    MarketingAgent,
    SalesAgent,
    DigitalAgent,
    EntertainmentAgent,
)


class TestPresets:
    def test_office_agent(self):
        agent = OfficeAgent()
        assert agent.name == "OfficeAgent"
        assert "document_processor" in agent.tool_names
        assert "email_handler" in agent.tool_names
        assert "data_entry" in agent.tool_names
        assert "spreadsheet_manager" in agent.tool_names

    def test_marketing_agent(self):
        agent = MarketingAgent()
        assert agent.name == "MarketingAgent"
        assert "content_creator" in agent.tool_names
        assert "campaign_manager" in agent.tool_names
        assert "analytics_tracker" in agent.tool_names

    def test_sales_agent(self):
        agent = SalesAgent()
        assert agent.name == "SalesAgent"
        assert "lead_generator" in agent.tool_names
        assert "outreach_manager" in agent.tool_names
        assert "crm_updater" in agent.tool_names

    def test_digital_agent(self):
        agent = DigitalAgent()
        assert agent.name == "DigitalAgent"
        assert "web_scraper" in agent.tool_names
        assert "seo_optimizer" in agent.tool_names
        assert "social_media_poster" in agent.tool_names

    def test_entertainment_agent(self):
        agent = EntertainmentAgent()
        assert agent.name == "EntertainmentAgent"
        assert "content_curator" in agent.tool_names
        assert "recommendation_engine" in agent.tool_names

    def test_preset_execute(self):
        agent = OfficeAgent()
        result = agent.execute(
            "document_processor",
            {"content": "test", "format": "pdf"},
        )
        assert result.success
        assert result.output["processed"] is True

    def test_custom_name(self):
        agent = OfficeAgent(name="CustomOffice")
        assert agent.name == "CustomOffice"
