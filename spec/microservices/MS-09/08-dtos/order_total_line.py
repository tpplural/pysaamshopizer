"""Pydantic v2 model for OrderTotalLine. Source schema: OrderTotalLine (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class OrderTotalLine(BaseModel):
    """Source schema: OrderTotalLine (04-api-contract.yaml)."""

    value: float
    sort_order: int
    module_code: str | None = None
    total_type: str | None = None
    code: str | None = None
    title: str | None = None
