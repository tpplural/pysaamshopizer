"""DTO for CartSummary (source: components/schemas/CartSummary in MS-06/04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel

from .order_total_line import OrderTotalLine


class CartSummary(BaseModel):
    code: str
    quantity: int
    sub_total: str
    total: str
    totals: list[OrderTotalLine]
