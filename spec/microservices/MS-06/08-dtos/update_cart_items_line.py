"""DTO for UpdateCartItemsLine (source: components/schemas/UpdateCartItemsLine in MS-06/04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UpdateCartItemsLine(BaseModel):
    item_id: str
    quantity: int = Field(ge=1)
