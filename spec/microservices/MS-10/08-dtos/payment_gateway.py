"""PaymentGateway DTO. Source schema: components/schemas/PaymentGateway (04-api-contract.yaml)."""
from __future__ import annotations

from pydantic import BaseModel


class PaymentGateway(BaseModel):
    code: str
    regions: list[str] | None = None
    operations: list[str] | None = None
