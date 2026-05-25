"""Tests for the TeamFactory auto-team creation."""

import pytest

from agentwork.factory import TeamFactory
from agentwork.orchestrator import CompanyOrchestrator


class TestTeamFactoryDetection:
    """Tests for keyword detection in TeamFactory."""

    def setup_method(self):
        self.factory = TeamFactory()

    def test_detect_product_sales(self):
        types = self.factory.detect_company_types("manage product inventory and pricing")
        assert "product_sales" in types

    def test_detect_marketing_agency(self):
        types = self.factory.detect_company_types("run a social media marketing campaign")
        assert "marketing_agency" in types

    def test_detect_data_solutions(self):
        types = self.factory.detect_company_types("run ETL pipeline and data analytics")
        assert "data_solutions" in types

    def test_detect_digital_agency(self):
        types = self.factory.detect_company_types("build a web app with frontend and backend")
        assert "digital_agency" in types

    def test_detect_entertainment(self):
        types = self.factory.detect_company_types("plan entertainment event and streaming distribution")
        assert "entertainment" in types

    def test_detect_no_match(self):
        types = self.factory.detect_company_types("something completely unrelated xyz")
        assert types == []

    def test_detect_no_substring_false_positive_data(self):
        """'data' should not match 'database' or 'update'."""
        types = self.factory.detect_company_types("update the database schema")
        assert "data_solutions" not in types

    def test_detect_no_substring_false_positive_app(self):
        """'app' should not match 'happy' or 'application'."""
        types = self.factory.detect_company_types("make the customer happy with our application")
        assert "digital_agency" not in types

    def test_detect_word_boundary_positive(self):
        """'data' should match when used as a standalone word."""
        types = self.factory.detect_company_types("process the data from sensors")
        assert "data_solutions" in types

    def test_detect_word_boundary_app_standalone(self):
        """'app' should match when it's a standalone word."""
        types = self.factory.detect_company_types("build an app for mobile users")
        assert "digital_agency" in types

    def test_detect_multiple_types(self):
        types = self.factory.detect_company_types("build a web app for marketing campaign analytics with data pipeline")
        assert len(types) >= 2


class TestTeamFactoryCreation:
    """Tests for team creation in TeamFactory."""

    def setup_method(self):
        self.factory = TeamFactory()

    def test_create_team_returns_orchestrator(self):
        orchestrator = self.factory.create_team("manage sales inventory and pricing")
        assert isinstance(orchestrator, CompanyOrchestrator)

    def test_create_team_product_sales(self):
        orchestrator = self.factory.create_team("manage product inventory and sales pricing for our commerce deals")
        agents = orchestrator.agents
        agent_names = [a.name for a in agents]
        assert any("ProductSales" in name for name in agent_names)

    def test_create_team_fallback_generic(self):
        orchestrator = self.factory.create_team("do something completely unknown xyz abc")
        agents = orchestrator.agents
        # Should have one agent from each company type (5 total)
        assert len(agents) == 5

    def test_create_team_mixed(self):
        # Task that matches multiple types roughly equally
        orchestrator = self.factory.create_team("marketing campaign with data analytics and reporting")
        agents = orchestrator.agents
        # Should have agents from multiple company types
        assert len(agents) > 5

    def test_create_team_has_tools(self):
        orchestrator = self.factory.create_team("manage product sales inventory and pricing for commerce")
        agents = orchestrator.agents
        all_tools = []
        for agent in agents:
            all_tools.extend(agent.tool_names)
        assert len(all_tools) > 0

    def test_orchestrator_can_dispatch(self):
        orchestrator = self.factory.create_team("manage product sales inventory and pricing for commerce")
        # Verify it can dispatch tasks to the agents
        status = orchestrator.get_status("nonexistent")
        assert status is None

    def test_create_team_digital_agency(self):
        orchestrator = self.factory.create_team("build web app frontend backend deploy qa testing devops")
        agents = orchestrator.agents
        agent_names = [a.name for a in agents]
        assert any("DigitalAgency" in name for name in agent_names)

    def test_create_team_entertainment(self):
        orchestrator = self.factory.create_team("plan entertainment streaming media distribution schedule event")
        agents = orchestrator.agents
        agent_names = [a.name for a in agents]
        assert any("Entertainment" in name for name in agent_names)
