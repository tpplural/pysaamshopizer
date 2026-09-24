"""DTO for CreateCartRequest (source: components/schemas/CreateCartRequest in MS-06/04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class CreateCartRequest(BaseModel):
    code: str | None = None
    store_id: str
    customer_id: str | None = None
