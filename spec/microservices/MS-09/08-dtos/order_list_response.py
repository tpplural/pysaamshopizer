"""Pydantic v2 model for OrderListResponse. Source schema: OrderListResponse (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel

from .order_summary_item import OrderSummaryItem
from .pagination_info import PaginationInfo


class OrderListResponse(BaseModel):
    """Source schema: OrderListResponse (04-api-contract.yaml)."""

    items: list[OrderSummaryItem] | None = None
    pagination: PaginationInfo | None = None


OrderListResponse.model_rebuild()
