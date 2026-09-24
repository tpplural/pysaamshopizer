"""Pydantic v2 model for CalculateOrderTotalRequest. Source schema: CalculateOrderTotalRequest (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel

from .customer_ref import CustomerRef
from .order_line_item import OrderLineItem
from .shipping_summary import ShippingSummary


class CalculateOrderTotalRequest(BaseModel):
    """Source schema: CalculateOrderTotalRequest (04-api-contract.yaml)."""

    cart_code: str | None = None
    items: list[OrderLineItem] | None = None
    shipping: ShippingSummary | None = None
    customer: CustomerRef | None = None


CalculateOrderTotalRequest.model_rebuild()
