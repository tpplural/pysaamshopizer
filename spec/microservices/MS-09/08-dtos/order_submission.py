"""Pydantic v2 model for OrderSubmission. Source schema: OrderSubmission (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel

from .address import Address
from .enums import PaymentType
from .payment_instruction import PaymentInstruction


class OrderSubmission(BaseModel):
    """Source schema: OrderSubmission (04-api-contract.yaml)."""

    billing: Address | None = None
    delivery: Address | None = None
    ship_to_billing_address: bool | None = None
    payment_type: PaymentType | None = None
    payment: PaymentInstruction | None = None
    selected_shipping_option: str | None = None


OrderSubmission.model_rebuild()
