"""DTO for UpdateCartItemsRequest (source: components/schemas/UpdateCartItemsRequest in MS-06/04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel

from .update_cart_items_line import UpdateCartItemsLine


class UpdateCartItemsRequest(BaseModel):
    items: list[UpdateCartItemsLine]
