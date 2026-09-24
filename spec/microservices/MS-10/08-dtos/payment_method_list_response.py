"""PaymentMethodListResponse DTO. Source schema: components/schemas/PaymentMethodListResponse (04-api-contract.yaml)."""
from __future__ import annotations

from pydantic import BaseModel

from .payment_method import PaymentMethod


class PaymentMethodListResponse(BaseModel):
    items: list[PaymentMethod] | None = None
