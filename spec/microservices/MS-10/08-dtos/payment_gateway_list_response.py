"""PaymentGatewayListResponse DTO. Source schema: components/schemas/PaymentGatewayListResponse (04-api-contract.yaml)."""
from __future__ import annotations

from pydantic import BaseModel

from .payment_gateway import PaymentGateway


class PaymentGatewayListResponse(BaseModel):
    items: list[PaymentGateway] | None = None
