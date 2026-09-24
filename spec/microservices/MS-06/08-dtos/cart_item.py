"""DTO for CartItem (source: components/schemas/CartItem in MS-06/04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel

from .cart_item_attribute import CartItemAttribute


class CartItem(BaseModel):
    id: str
    product_id: str
    quantity: int
    unit_price: float | None = None
    sub_total: float | None = None
    product_virtual: bool | None = None
    attributes: list[CartItemAttribute] | None = None
