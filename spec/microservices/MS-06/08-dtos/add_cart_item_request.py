"""DTO for AddCartItemRequest (source: components/schemas/AddCartItemRequest in MS-06/04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel

from .add_cart_item_attribute import AddCartItemAttribute


class AddCartItemRequest(BaseModel):
    product_id: str
    quantity: int = 1
    attributes: list[AddCartItemAttribute] | None = None
