"""PaymentMethod DTO. Source schema: components/schemas/PaymentMethod (04-api-contract.yaml)."""
from __future__ import annotations

from pydantic import BaseModel

from .enums import PaymentType


class PaymentMethod(BaseModel):
    code: str
    payment_type: PaymentType
    default_selected: bool | None = None
