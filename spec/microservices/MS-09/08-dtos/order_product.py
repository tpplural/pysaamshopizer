"""Pydantic v2 model for OrderProduct. Source schema: OrderProduct (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class OrderProduct(BaseModel):
    """Source schema: OrderProduct (04-api-contract.yaml)."""

    order_product_id: str | None = None
    sku: str | None = None
    product_name: str | None = None
    quantity: int | None = None
    one_time_charge: float | None = None
