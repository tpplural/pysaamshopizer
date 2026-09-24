"""Pydantic v2 model for PaymentInstruction. Source schema: PaymentInstruction (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel

from .enums import PaymentType


class PaymentInstruction(BaseModel):
    """Source schema: PaymentInstruction (04-api-contract.yaml)."""

    payment_type: PaymentType
    module_name: str | None = None
    number: str | None = None
    holder: str | None = None
    cvv: str | None = None
    expiry_month: int | None = None
    expiry_year: int | None = None
    card_type: str | None = None
