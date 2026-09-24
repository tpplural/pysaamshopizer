"""InitializePaymentRequest DTO. Source schema: components/schemas/InitializePaymentRequest (04-api-contract.yaml)."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class InitializePaymentRequest(BaseModel):
    order_id: str
    module_name: str
    amount: Decimal  # money: NUMERIC(19,4) per 02-domain-model.md (transaction.amount)
