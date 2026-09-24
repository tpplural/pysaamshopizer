"""DTO for UpdateCartItemRequest (source: components/schemas/UpdateCartItemRequest in MS-06/04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(ge=1)
