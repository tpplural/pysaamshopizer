"""PaymentErrorResponse DTO. Source schema: components/schemas/PaymentErrorResponse (04-api-contract.yaml),
allOf composing the shared ErrorResponse (spec/shared/common-schemas.yaml#/components/schemas/ErrorResponse)
plus the payment-specific additive field message_key. The shared base shape is modeled locally per the
$ref-handling rule."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PaymentErrorResponse(BaseModel):
    # Fields flattened from shared ErrorResponse (required: error, message, status_code).
    error: str
    message: str
    status_code: int
    timestamp: datetime | None = None
    # Payment-specific additive field.
    message_key: str | None = None
