"""ProductType model from MS-04 04-api-contract.yaml components/schemas/ProductType."""
from __future__ import annotations

from pydantic import BaseModel


class ProductType(BaseModel):
    code: str | None = None
    allow_add_to_cart: bool | None = None
