"""InitializationToken DTO. Source schema: components/schemas/InitializationToken (04-api-contract.yaml)."""
from __future__ import annotations

from pydantic import BaseModel

from .enums import TransactionType


class InitializationToken(BaseModel):
    transaction_type: TransactionType
    token: str
    persisted: bool
