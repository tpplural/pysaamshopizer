"""Enums for MS-09 order-service DTOs. Source: 04-api-contract.yaml components/schemas (OrderStatus, PaymentType)."""

from __future__ import annotations

from enum import Enum


class OrderStatus(str, Enum):
    """Source schema: OrderStatus (04-api-contract.yaml)."""

    ORDERED = "Ordered"
    PROCESSED = "Processed"
    DELIVERED = "Delivered"
    REFUNDED = "Refunded"


class PaymentType(str, Enum):
    """Source schema: PaymentType (04-api-contract.yaml)."""

    CREDIT_CARD = "CreditCard"
    FREE = "Free"
    COD = "Cod"
    MONEY_ORDER = "MoneyOrder"
    PAYPAL = "Paypal"
