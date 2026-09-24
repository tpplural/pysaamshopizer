"""Pydantic v2 model for OrderTotalSummary. Source schema: OrderTotalSummary (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel

from .order_total_line import OrderTotalLine


class OrderTotalSummary(BaseModel):
    """Source schema: OrderTotalSummary (04-api-contract.yaml)."""

    sub_total: float | None = None
    tax_total: float | None = None
    total: float | None = None
    totals: list[OrderTotalLine] | None = None


OrderTotalSummary.model_rebuild()
