"""TransactionListResponse DTO. Source schema: components/schemas/TransactionListResponse (04-api-contract.yaml)."""
from __future__ import annotations

from pydantic import BaseModel

from .transaction import Transaction


class TransactionListResponse(BaseModel):
    items: list[Transaction] | None = None
