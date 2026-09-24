"""Pydantic v2 model for ShippingSummary. Source schema: ShippingSummary (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class ShippingSummary(BaseModel):
    """Source schema: ShippingSummary (04-api-contract.yaml)."""

    free_shipping: bool | None = None
    tax_on_shipping: bool | None = None
    handling: float | None = None
    shipping: float | None = None
    shipping_option: str | None = None
    shipping_module: str | None = None
