"""Pydantic v2 model for CheckoutContext. Source schema: CheckoutContext (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel

from .address import Address
from .order_total_summary import OrderTotalSummary


class CheckoutPaymentMethod(BaseModel):
    """Inline object: CheckoutContext.payment_methods[] (04-api-contract.yaml)."""

    code: str | None = None
    default: bool | None = None


class CheckoutContextCustomer(BaseModel):
    """Inline object: CheckoutContext.customer (04-api-contract.yaml)."""

    billing: Address | None = None
    delivery: Address | None = None


class CheckoutContext(BaseModel):
    """Source schema: CheckoutContext (04-api-contract.yaml)."""

    cart_code: str | None = None
    payment_methods: list[CheckoutPaymentMethod] | None = None
    customer: CheckoutContextCustomer | None = None
    totals: OrderTotalSummary | None = None


CheckoutContext.model_rebuild()
