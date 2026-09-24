"""Pydantic v2 model for OrderStatusHistoryEntry. Source schema: OrderStatusHistoryEntry (04-api-contract.yaml)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from .enums import OrderStatus


class OrderStatusHistoryEntry(BaseModel):
    """Source schema: OrderStatusHistoryEntry (04-api-contract.yaml)."""

    status: OrderStatus | None = None
    date: datetime | None = None
    customer_notified: bool | None = None
    comment: str | None = None


OrderStatusHistoryEntry.model_rebuild()
