"""Transaction DTO. Source schema: components/schemas/Transaction (04-api-contract.yaml)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from .enums import PaymentType, TransactionType


class Transaction(BaseModel):
    transaction_id: str
    transaction_type: TransactionType
    order_id: str | None = None
    amount: Decimal | None = None  # money: NUMERIC(19,4) per 02-domain-model.md (transaction.amount)
    currency: str | None = None
    payment_type: PaymentType | None = None
    payment_module_code: str | None = None
    transaction_date: datetime | None = None
    details: dict[str, str] | None = None
    event_published: str | None = None
    persisted: bool | None = None
    partial: bool | None = None
