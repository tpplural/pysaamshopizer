"""Pydantic v2 model for OrderLineItem. Source schema: OrderLineItem (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class OrderLineItem(BaseModel):
    """Source schema: OrderLineItem (04-api-contract.yaml)."""

    unit_price: float
    quantity: int
    sku: str | None = None
    product_name: str | None = None
