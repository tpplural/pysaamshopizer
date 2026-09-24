"""Pydantic v2 model for RefundRequest. Source schema: RefundRequest (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class RefundRequest(BaseModel):
    """Source schema: RefundRequest (04-api-contract.yaml)."""

    amount: float
