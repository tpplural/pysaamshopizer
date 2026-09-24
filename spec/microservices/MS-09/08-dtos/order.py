"""Pydantic v2 model for Order aggregate. Source schema: Order (04-api-contract.yaml)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from .address import Address
from .enums import OrderStatus, PaymentType
from .masked_card import MaskedCard
from .order_product import OrderProduct
from .order_status_history_entry import OrderStatusHistoryEntry
from .order_total_line import OrderTotalLine


class Order(BaseModel):
    """Source schema: Order (04-api-contract.yaml)."""

    order_id: str
    status: OrderStatus
    total: float | None = None
    currency: str | None = None
    customer_id: str | None = None
    customer_email: str | None = None
    store_id: str | None = None
    date_purchased: date | None = None
    payment_type: PaymentType | None = None
    payment: MaskedCard | None = None
    billing: Address | None = None
    delivery: Address | None = None
    products: list[OrderProduct] | None = None
    totals: list[OrderTotalLine] | None = None
    status_history: list[OrderStatusHistoryEntry] | None = None


Order.model_rebuild()
