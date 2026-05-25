"""Tests for company fleet presets."""

import pytest

from agentwork.presets.companies.product_sales import ProductSalesCompany
from agentwork.presets.companies.marketing_agency import MarketingAgencyCompany
from agentwork.presets.companies.data_solutions import DataSolutionsCompany
from agentwork.presets.companies.digital_agency import DigitalAgencyCompany
from agentwork.presets.companies.entertainment_company import EntertainmentCompany


class TestProductSalesCompany:
    """Tests for the ProductSalesCompany fleet."""

    def test_returns_correct_number_of_agents(self):
        agents = ProductSalesCompany()
        assert len(agents) == 4

    def test_agent_names_with_default_prefix(self):
        agents = ProductSalesCompany()
        names = [a.name for a in agents]
        assert "ProductSales_ProductManager" in names
        assert "ProductSales_SalesRep" in names
        assert "ProductSales_OrderFulfillment" in names
        assert "ProductSales_CustomerSuccess" in names

    def test_custom_prefix(self):
        agents = ProductSalesCompany(prefix="MySales")
        names = [a.name for a in agents]
        assert "MySales_ProductManager" in names
        assert "MySales_SalesRep" in names

    def test_product_manager_tools(self):
        agents = ProductSalesCompany()
        pm = next(a for a in agents if "ProductManager" in a.name)
        tool_names = pm.tool_names
        assert "product_catalog" in tool_names
        assert "pricing_engine" in tool_names
        assert "inventory_checker" in tool_names

    def test_sales_rep_tools(self):
        agents = ProductSalesCompany()
        sr = next(a for a in agents if "SalesRep" in a.name)
        tool_names = sr.tool_names
        assert "sales_pipeline" in tool_names
        assert "deal_closer" in tool_names
        assert "quote_generator" in tool_names

    def test_order_fulfillment_tools(self):
        agents = ProductSalesCompany()
        of = next(a for a in agents if "OrderFulfillment" in a.name)
        tool_names = of.tool_names
        assert "order_processor" in tool_names
        assert "shipping_tracker" in tool_names
        assert "invoice_generator" in tool_names

    def test_customer_success_tools(self):
        agents = ProductSalesCompany()
        cs = next(a for a in agents if "CustomerSuccess" in a.name)
        tool_names = cs.tool_names
        assert "account_manager" in tool_names
        assert "renewal_tracker" in tool_names
        assert "upsell_identifier" in tool_names

    def test_tool_execution_product_catalog(self):
        agents = ProductSalesCompany()
        pm = next(a for a in agents if "ProductManager" in a.name)
        result = pm.execute("product_catalog", {"query": "shoes", "category": "footwear"})
        assert result.success
        assert result.output["status"] == "success"

    def test_tool_execution_deal_closer(self):
        agents = ProductSalesCompany()
        sr = next(a for a in agents if "SalesRep" in a.name)
        result = sr.execute("deal_closer", {"deal_id": "D123", "terms": "net30"})
        assert result.success
        assert result.output["status"] == "closed"

    def test_agents_have_capabilities(self):
        agents = ProductSalesCompany()
        pm = next(a for a in agents if "ProductManager" in a.name)
        assert "product" in pm.capabilities
        assert "pricing" in pm.capabilities


class TestMarketingAgencyCompany:
    """Tests for the MarketingAgencyCompany fleet."""

    def test_returns_correct_number_of_agents(self):
        agents = MarketingAgencyCompany()
        assert len(agents) == 5

    def test_agent_names_with_default_prefix(self):
        agents = MarketingAgencyCompany()
        names = [a.name for a in agents]
        assert "MarketingAgency_CampaignStrategist" in names
        assert "MarketingAgency_SocialMediaManager" in names
        assert "MarketingAgency_SEOSpecialist" in names
        assert "MarketingAgency_ContentProducer" in names
        assert "MarketingAgency_AdBuyer" in names

    def test_campaign_strategist_tools(self):
        agents = MarketingAgencyCompany()
        cs = next(a for a in agents if "CampaignStrategist" in a.name)
        tool_names = cs.tool_names
        assert "campaign_planner" in tool_names
        assert "audience_segmenter" in tool_names
        assert "budget_allocator" in tool_names

    def test_tool_execution_roi_calculator(self):
        agents = MarketingAgencyCompany()
        ab = next(a for a in agents if "AdBuyer" in a.name)
        result = ab.execute("roi_calculator", {"spend": 100.0, "revenue": 250.0})
        assert result.success
        assert result.output["roi_percent"] == 150.0

    def test_custom_prefix(self):
        agents = MarketingAgencyCompany(prefix="MyAgency")
        names = [a.name for a in agents]
        assert "MyAgency_CampaignStrategist" in names


class TestDataSolutionsCompany:
    """Tests for the DataSolutionsCompany fleet."""

    def test_returns_correct_number_of_agents(self):
        agents = DataSolutionsCompany()
        assert len(agents) == 5

    def test_agent_names_with_default_prefix(self):
        agents = DataSolutionsCompany()
        names = [a.name for a in agents]
        assert "DataSolutions_DataEngineer" in names
        assert "DataSolutions_DataAnalyst" in names
        assert "DataSolutions_DataCleaner" in names
        assert "DataSolutions_ReportGenerator" in names
        assert "DataSolutions_MLEngineer" in names

    def test_data_engineer_tools(self):
        agents = DataSolutionsCompany()
        de = next(a for a in agents if "DataEngineer" in a.name)
        tool_names = de.tool_names
        assert "data_ingester" in tool_names
        assert "etl_pipeline" in tool_names
        assert "schema_validator" in tool_names

    def test_tool_execution_etl_pipeline(self):
        agents = DataSolutionsCompany()
        de = next(a for a in agents if "DataEngineer" in a.name)
        result = de.execute("etl_pipeline", {"pipeline_name": "daily_sync", "source": "db", "destination": "warehouse"})
        assert result.success
        assert result.output["status"] == "completed"

    def test_ml_engineer_tools(self):
        agents = DataSolutionsCompany()
        ml = next(a for a in agents if "MLEngineer" in a.name)
        tool_names = ml.tool_names
        assert "model_trainer" in tool_names
        assert "prediction_runner" in tool_names
        assert "feature_extractor" in tool_names


class TestDigitalAgencyCompany:
    """Tests for the DigitalAgencyCompany fleet."""

    def test_returns_correct_number_of_agents(self):
        agents = DigitalAgencyCompany()
        assert len(agents) == 5

    def test_agent_names_with_default_prefix(self):
        agents = DigitalAgencyCompany()
        names = [a.name for a in agents]
        assert "DigitalAgency_FrontendDev" in names
        assert "DigitalAgency_BackendDev" in names
        assert "DigitalAgency_QAEngineer" in names
        assert "DigitalAgency_DevOpsEngineer" in names
        assert "DigitalAgency_UXDesigner" in names

    def test_frontend_dev_tools(self):
        agents = DigitalAgencyCompany()
        fd = next(a for a in agents if "FrontendDev" in a.name)
        tool_names = fd.tool_names
        assert "ui_builder" in tool_names
        assert "responsive_tester" in tool_names
        assert "accessibility_checker" in tool_names

    def test_tool_execution_deployer(self):
        agents = DigitalAgencyCompany()
        devops = next(a for a in agents if "DevOpsEngineer" in a.name)
        result = devops.execute("deployer", {"app_name": "myapp", "environment": "production", "version": "1.0"})
        assert result.success
        assert result.output["status"] == "deployed"

    def test_custom_prefix(self):
        agents = DigitalAgencyCompany(prefix="TechCo")
        names = [a.name for a in agents]
        assert "TechCo_FrontendDev" in names
        assert "TechCo_BackendDev" in names


class TestEntertainmentCompany:
    """Tests for the EntertainmentCompany fleet."""

    def test_returns_correct_number_of_agents(self):
        agents = EntertainmentCompany()
        assert len(agents) == 4

    def test_agent_names_with_default_prefix(self):
        agents = EntertainmentCompany()
        names = [a.name for a in agents]
        assert "Entertainment_ContentProducer" in names
        assert "Entertainment_Scheduler" in names
        assert "Entertainment_Distributor" in names
        assert "Entertainment_AudienceManager" in names

    def test_content_producer_tools(self):
        agents = EntertainmentCompany()
        cp = next(a for a in agents if "ContentProducer" in a.name)
        tool_names = cp.tool_names
        assert "script_writer" in tool_names
        assert "scene_planner" in tool_names
        assert "talent_coordinator" in tool_names

    def test_tool_execution_script_writer(self):
        agents = EntertainmentCompany()
        cp = next(a for a in agents if "ContentProducer" in a.name)
        result = cp.execute("script_writer", {"title": "My Show", "genre": "drama"})
        assert result.success
        assert result.output["status"] == "written"

    def test_distributor_tools(self):
        agents = EntertainmentCompany()
        dist = next(a for a in agents if "Distributor" in a.name)
        tool_names = dist.tool_names
        assert "platform_publisher" in tool_names
        assert "syndication_manager" in tool_names
        assert "rights_tracker" in tool_names

    def test_agents_have_capabilities(self):
        agents = EntertainmentCompany()
        sched = next(a for a in agents if "Scheduler" in a.name)
        assert "scheduling" in sched.capabilities
        assert "events" in sched.capabilities
