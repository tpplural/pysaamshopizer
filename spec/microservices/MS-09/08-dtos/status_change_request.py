"""Pydantic v2 model for StatusChangeRequest. Source schema: StatusChangeRequest (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel

from .enums import OrderStatus


class StatusChangeRequest(BaseModel):
    """Source schema: StatusChangeRequest (04-api-contract.yaml)."""

    status: OrderStatus
    comment: str | None = None
    customer_notified: bool | None = None
    customer_email_address: str | None = None


StatusChangeRequest.model_rebuild()
