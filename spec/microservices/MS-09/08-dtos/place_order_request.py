"""Pydantic v2 model for PlaceOrderRequest. Source schema: PlaceOrderRequest (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel

from .address import Address
from .order_line_item import OrderLineItem
from .payment_instruction import PaymentInstruction


class PlaceOrderCustomer(BaseModel):
    """Inline object: PlaceOrderRequest.customer (04-api-contract.yaml)."""

    customer_id: str | None = None
    billing: Address | None = None
    delivery: Address | None = None


class PlaceOrderRequest(BaseModel):
    """Source schema: PlaceOrderRequest (04-api-contract.yaml)."""

    payment: PaymentInstruction
    cart_code: str | None = None
    idempotency_key: str | None = None
    ship_to_billing_address: bool | None = None
    customer: PlaceOrderCustomer | None = None
    items: list[OrderLineItem] | None = None


PlaceOrderRequest.model_rebuild()
