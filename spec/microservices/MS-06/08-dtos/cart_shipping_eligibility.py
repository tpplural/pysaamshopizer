"""DTO for CartShippingEligibility (source: components/schemas/CartShippingEligibility in MS-06/04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel

from .shippable_item import ShippableItem


class CartShippingEligibility(BaseModel):
    requires_shipping: bool
    free_cart: bool
    shippable_items: list[ShippableItem]
