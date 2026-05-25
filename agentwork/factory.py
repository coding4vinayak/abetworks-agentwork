"""TeamFactory - automatically creates the right team of agents for any given task."""

from __future__ import annotations

from typing import Any, Dict, List

from agentwork.core.agent import Agent
from agentwork.orchestrator import CompanyOrchestrator
from agentwork.presets.companies.product_sales import ProductSalesCompany
from agentwork.presets.companies.marketing_agency import MarketingAgencyCompany
from agentwork.presets.companies.data_solutions import DataSolutionsCompany
from agentwork.presets.companies.digital_agency import DigitalAgencyCompany
from agentwork.presets.companies.entertainment_company import EntertainmentCompany


class TeamFactory:
    """Creates the right team of agents for any given task description.

    Analyzes task descriptions using keyword matching to select the most
    appropriate company type(s) and returns a CompanyOrchestrator with
    the selected agents ready to execute.
    """

    KEYWORD_MAP: Dict[str, List[str]] = {
        "product_sales": [
            "product", "sales", "selling", "inventory", "order",
            "pricing", "commerce", "revenue", "deal", "quote",
        ],
        "marketing_agency": [
            "marketing", "campaign", "social media", "seo", "content",
            "advertising", "brand", "engagement", "audience",
        ],
        "data_solutions": [
            "data", "analytics", "etl", "pipeline", "cleaning",
            "reporting", "ml", "machine learning", "statistics", "query",
        ],
        "digital_agency": [
            "web", "app", "frontend", "backend", "deploy",
            "qa", "testing", "devops", "ui", "ux", "development",
        ],
        "entertainment": [
            "entertainment", "content production", "streaming", "audience",
            "distribution", "media", "schedule", "event",
        ],
    }

    COMPANY_FACTORIES = {
        "product_sales": ProductSalesCompany,
        "marketing_agency": MarketingAgencyCompany,
        "data_solutions": DataSolutionsCompany,
        "digital_agency": DigitalAgencyCompany,
        "entertainment": EntertainmentCompany,
    }

    def detect_company_types(self, task_description: str) -> List[str]:
        """Return which company types match the task description, ordered by score.

        Args:
            task_description: Human-readable description of the task.

        Returns:
            List of company type keys sorted by match score (highest first).
        """
        task_lower = task_description.lower()
        scores: Dict[str, int] = {}

        for company_type, keywords in self.KEYWORD_MAP.items():
            score = 0
            for keyword in keywords:
                if keyword in task_lower:
                    score += 1
            if score > 0:
                scores[company_type] = score

        # Sort by score descending
        return sorted(scores.keys(), key=lambda k: scores[k], reverse=True)

    def create_team(self, task_description: str) -> CompanyOrchestrator:
        """Analyze task description and create appropriate team.

        Scores each company type by counting keyword matches. If one type
        clearly dominates, uses only that company's agents. If multiple
        types are relevant, mixes agents from the top-scoring types.
        If no keywords match, returns a generic team with one agent from
        each company type.

        Args:
            task_description: Human-readable description of the task.

        Returns:
            CompanyOrchestrator with selected agents registered.
        """
        matched_types = self.detect_company_types(task_description)

        if not matched_types:
            # No matches - create a generic team with one agent from each company
            agents: List[Agent] = []
            for factory in self.COMPANY_FACTORIES.values():
                company_agents = factory()
                if company_agents:
                    agents.append(company_agents[0])
            return CompanyOrchestrator(agents=agents)

        # Score to determine if one type dominates
        task_lower = task_description.lower()
        scores: Dict[str, int] = {}
        for company_type in matched_types:
            score = 0
            for keyword in self.KEYWORD_MAP[company_type]:
                if keyword in task_lower:
                    score += 1
            scores[company_type] = score

        top_score = scores[matched_types[0]]
        # If top scorer has at least double the second scorer, use only that type
        if len(matched_types) == 1 or top_score >= 2 * scores.get(matched_types[1], 0):
            agents = self.COMPANY_FACTORIES[matched_types[0]]()
        else:
            # Mix agents from top-scoring types
            agents = []
            for company_type in matched_types:
                company_agents = self.COMPANY_FACTORIES[company_type]()
                agents.extend(company_agents)

        return CompanyOrchestrator(agents=agents)
