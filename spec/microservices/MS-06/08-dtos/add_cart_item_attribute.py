"""DTO for AddCartItemAttribute (source: components/schemas/AddCartItemAttribute in MS-06/04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class AddCartItemAttribute(BaseModel):
    attribute_id: str
