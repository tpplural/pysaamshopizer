"""RefundRequest DTO. Source schema: components/schemas/RefundRequest (04-api-contract.yaml)."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class RefundRequest(BaseModel):
    amount: Decimal  # money: NUMERIC(19,4) per 02-domain-model.md (transaction.amount)
