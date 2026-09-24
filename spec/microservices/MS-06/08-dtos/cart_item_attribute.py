"""DTO for CartItemAttribute (source: components/schemas/CartItemAttribute in MS-06/04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class CartItemAttribute(BaseModel):
    id: str | None = None
    attribute_id: str
    option_name: str | None = None
    option_value: str | None = None
