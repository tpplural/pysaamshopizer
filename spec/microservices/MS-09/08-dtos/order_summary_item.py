"""Pydantic v2 model for OrderSummaryItem. Source schema: OrderSummaryItem (04-api-contract.yaml)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from .enums import OrderStatus


class OrderSummaryItem(BaseModel):
    """Source schema: OrderSummaryItem (04-api-contract.yaml)."""

    order_id: str | None = None
    status: OrderStatus | None = None
    total: float | None = None
    date_purchased: date | None = None
    customer_email: str | None = None


OrderSummaryItem.model_rebuild()
