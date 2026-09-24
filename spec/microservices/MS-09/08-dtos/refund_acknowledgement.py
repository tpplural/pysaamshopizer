"""Pydantic v2 model for RefundAcknowledgement. Source schema: RefundAcknowledgement (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class RefundAcknowledgement(BaseModel):
    """Source schema: RefundAcknowledgement (04-api-contract.yaml)."""

    order_id: str | None = None
    refund_requested: float | None = None
    status: str | None = None
