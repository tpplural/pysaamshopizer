"""Pydantic v2 model for PreAuthorizationRequest. Source schema: PreAuthorizationRequest (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel

from .payment_instruction import PaymentInstruction


class PreAuthorizationRequest(BaseModel):
    """Source schema: PreAuthorizationRequest (04-api-contract.yaml)."""

    cart_code: str
    payment: PaymentInstruction | None = None


PreAuthorizationRequest.model_rebuild()
