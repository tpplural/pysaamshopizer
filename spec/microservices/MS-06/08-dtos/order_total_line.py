"""DTO for OrderTotalLine (source: components/schemas/OrderTotalLine in MS-06/04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class OrderTotalLine(BaseModel):
    code: str
    value: float
