"""Pydantic v2 model for ShippingSummaryRequest. Source schema: ShippingSummaryRequest (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class SelectedShippingOption(BaseModel):
    """Inline object: ShippingSummaryRequest.selected_shipping_option (04-api-contract.yaml)."""

    code: str | None = None
    option_price: float | None = None


class ShippingSummaryRequest(BaseModel):
    """Source schema: ShippingSummaryRequest (04-api-contract.yaml)."""

    selected_shipping_option: SelectedShippingOption | None = None
    apply_tax_on_shipping: bool | None = None
    handling_fees: float | None = None
    free_shipping: bool | None = None


ShippingSummaryRequest.model_rebuild()
