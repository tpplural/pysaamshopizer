"""Pydantic v2 model for SaveOrderRequest. Source schema: SaveOrderRequest (04-api-contract.yaml)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from .address import Address
from .enums import OrderStatus


class SaveOrderRequest(BaseModel):
    """Source schema: SaveOrderRequest (04-api-contract.yaml)."""

    status: OrderStatus | None = None
    billing: Address | None = None
    delivery: Address | None = None
    customer_email: str | None = None
    date_purchased: date | None = None


SaveOrderRequest.model_rebuild()
