"""Pydantic v2 model for IntegrationOrderRequest. Source schema: IntegrationOrderRequest (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel

from .customer_ref import CustomerRef
from .order_line_item import OrderLineItem


class IntegrationOrderRequest(BaseModel):
    """Source schema: IntegrationOrderRequest (04-api-contract.yaml)."""

    customer: CustomerRef | None = None
    products: list[OrderLineItem] | None = None


IntegrationOrderRequest.model_rebuild()
