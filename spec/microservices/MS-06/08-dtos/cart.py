"""DTO for Cart (source: components/schemas/Cart in MS-06/04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel

from .cart_item import CartItem


class Cart(BaseModel):
    id: str
    code: str
    store_id: str
    customer_id: str | None = None
    quantity: int
    sub_total: str | None = None
    total: str | None = None
    items: list[CartItem]
