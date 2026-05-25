"""Company fleet presets - pre-configured teams of agents for specific business domains."""

from agentwork.presets.companies.product_sales import ProductSalesCompany
from agentwork.presets.companies.marketing_agency import MarketingAgencyCompany
from agentwork.presets.companies.data_solutions import DataSolutionsCompany
from agentwork.presets.companies.digital_agency import DigitalAgencyCompany
from agentwork.presets.companies.entertainment_company import EntertainmentCompany

__all__ = [
    "ProductSalesCompany",
    "MarketingAgencyCompany",
    "DataSolutionsCompany",
    "DigitalAgencyCompany",
    "EntertainmentCompany",
]
