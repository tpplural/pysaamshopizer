"""PaymentConfigListResponse DTO. Source schema: components/schemas/PaymentConfigListResponse (04-api-contract.yaml)."""
from __future__ import annotations

from pydantic import BaseModel

from .payment_config import PaymentConfig


class PaymentConfigListResponse(BaseModel):
    items: list[PaymentConfig] | None = None
