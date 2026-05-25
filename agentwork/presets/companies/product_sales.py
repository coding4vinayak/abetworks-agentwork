"""Product sales company fleet preset with specialized agents for sales workflows."""

from __future__ import annotations

from typing import Any, Dict, List

from agentwork.core.agent import Agent
from agentwork.tools.decorators import tool


# --- ProductManager tools ---

@tool(name="product_catalog", description="Manage and query the product catalog", retry_attempts=2)
def product_catalog(query: str = "", category: str = "") -> Dict[str, Any]:
    """Query or manage the product catalog."""
    return {"query": query, "category": category, "results": [], "status": "success"}


@tool(name="pricing_engine", description="Calculate and manage product pricing", retry_attempts=2)
def pricing_engine(product_id: str = "", discount: float = 0.0) -> Dict[str, Any]:
    """Calculate pricing for products."""
    return {"product_id": product_id, "discount": discount, "final_price": 0.0, "status": "calculated"}


@tool(name="inventory_checker", description="Check product inventory levels", retry_attempts=2)
def inventory_checker(product_id: str = "", warehouse: str = "main") -> Dict[str, Any]:
    """Check inventory levels for a product."""
    return {"product_id": product_id, "warehouse": warehouse, "quantity": 0, "status": "checked"}


# --- SalesRep tools ---

@tool(name="sales_pipeline", description="Manage and track the sales pipeline", retry_attempts=2)
def sales_pipeline(stage: str = "prospecting", lead_id: str = "") -> Dict[str, Any]:
    """Track leads through the sales pipeline."""
    return {"stage": stage, "lead_id": lead_id, "status": "updated"}


@tool(name="deal_closer", description="Facilitate and close deals", retry_attempts=3)
def deal_closer(deal_id: str = "", terms: str = "") -> Dict[str, Any]:
    """Close a deal with specified terms."""
    return {"deal_id": deal_id, "terms": terms, "status": "closed"}


@tool(name="quote_generator", description="Generate price quotes for customers", retry_attempts=2)
def quote_generator(items: List[str] = None, customer_id: str = "") -> Dict[str, Any]:
    """Generate a quote for a customer."""
    return {"items": items or [], "customer_id": customer_id, "quote_total": 0.0, "status": "generated"}


# --- OrderFulfillment tools ---

@tool(name="order_processor", description="Process and validate customer orders", retry_attempts=3)
def order_processor(order_id: str = "", items: List[str] = None) -> Dict[str, Any]:
    """Process a customer order."""
    return {"order_id": order_id, "items": items or [], "status": "processed"}


@tool(name="shipping_tracker", description="Track shipment status and logistics", retry_attempts=2)
def shipping_tracker(tracking_id: str = "", carrier: str = "") -> Dict[str, Any]:
    """Track a shipment."""
    return {"tracking_id": tracking_id, "carrier": carrier, "location": "warehouse", "status": "in_transit"}


@tool(name="invoice_generator", description="Generate invoices for completed orders", retry_attempts=2)
def invoice_generator(order_id: str = "", amount: float = 0.0) -> Dict[str, Any]:
    """Generate an invoice for an order."""
    return {"order_id": order_id, "amount": amount, "invoice_number": "", "status": "generated"}


# --- CustomerSuccess tools ---

@tool(name="account_manager", description="Manage customer accounts and relationships", retry_attempts=2)
def account_manager(account_id: str = "", action: str = "review") -> Dict[str, Any]:
    """Manage a customer account."""
    return {"account_id": account_id, "action": action, "status": "managed"}


@tool(name="renewal_tracker", description="Track subscription renewals and expirations", retry_attempts=2)
def renewal_tracker(account_id: str = "", renewal_date: str = "") -> Dict[str, Any]:
    """Track renewal status for an account."""
    return {"account_id": account_id, "renewal_date": renewal_date, "status": "tracked"}


@tool(name="upsell_identifier", description="Identify upsell and cross-sell opportunities", retry_attempts=2)
def upsell_identifier(account_id: str = "", current_plan: str = "") -> Dict[str, Any]:
    """Identify upsell opportunities for an account."""
    return {"account_id": account_id, "current_plan": current_plan, "opportunities": [], "status": "identified"}


def ProductSalesCompany(prefix: str = "ProductSales") -> List[Agent]:
    """Create a product sales company fleet with specialized agents.

    Returns a list of agents:
    - ProductManager: product catalog, pricing, and inventory management
    - SalesRep: pipeline management, deal closing, and quote generation
    - OrderFulfillment: order processing, shipping, and invoicing
    - CustomerSuccess: account management, renewals, and upselling
    """
    return [
        Agent(
            name=f"{prefix}_ProductManager",
            description="Product management agent for catalog, pricing, and inventory",
            tools=[product_catalog, pricing_engine, inventory_checker],
            capabilities=["product", "pricing", "inventory", "catalog"],
        ),
        Agent(
            name=f"{prefix}_SalesRep",
            description="Sales representative agent for pipeline, deals, and quotes",
            tools=[sales_pipeline, deal_closer, quote_generator],
            capabilities=["sales", "deals", "quotes", "pipeline"],
        ),
        Agent(
            name=f"{prefix}_OrderFulfillment",
            description="Order fulfillment agent for processing, shipping, and invoicing",
            tools=[order_processor, shipping_tracker, invoice_generator],
            capabilities=["orders", "shipping", "invoicing", "fulfillment"],
        ),
        Agent(
            name=f"{prefix}_CustomerSuccess",
            description="Customer success agent for accounts, renewals, and upselling",
            tools=[account_manager, renewal_tracker, upsell_identifier],
            capabilities=["accounts", "renewals", "upselling", "customer_success"],
        ),
    ]
