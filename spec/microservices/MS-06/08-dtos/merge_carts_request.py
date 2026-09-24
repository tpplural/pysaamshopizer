"""DTO for MergeCartsRequest (source: components/schemas/MergeCartsRequest in MS-06/04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class MergeCartsRequest(BaseModel):
    user_cart_code: str
    session_cart_code: str
    customer_id: str | None = None
