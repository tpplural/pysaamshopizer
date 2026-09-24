"""Pydantic v2 model for OrderConfirmation. Source schema: OrderConfirmation (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel

from .order_product_download import OrderProductDownload


class OrderConfirmation(BaseModel):
    """Source schema: OrderConfirmation (04-api-contract.yaml)."""

    order_id: str | None = None
    just_confirmed: bool | None = None
    total: float | None = None
    downloads: list[OrderProductDownload] | None = None


OrderConfirmation.model_rebuild()
