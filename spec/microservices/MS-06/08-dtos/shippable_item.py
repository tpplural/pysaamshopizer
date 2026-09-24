"""DTO for ShippableItem (source: components/schemas/ShippableItem in MS-06/04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class ShippableItem(BaseModel):
    product_id: str
    quantity: int
