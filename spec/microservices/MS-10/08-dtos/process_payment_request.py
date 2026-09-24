"""ProcessPaymentRequest DTO. Source schema: components/schemas/ProcessPaymentRequest (04-api-contract.yaml)."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from .credit_card import CreditCard
from .enums import PaymentType


class ProcessPaymentRequest(BaseModel):
    order_id: str
    module_name: str
    amount: Decimal  # money: NUMERIC(19,4) per 02-domain-model.md (transaction.amount)
    payment_type: PaymentType | None = None
    card: CreditCard | None = None
    payer_id: str | None = None
    payment_token: str | None = None
