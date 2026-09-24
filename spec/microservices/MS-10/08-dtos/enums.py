"""Enum types for MS-10 payment service. Source: 04-api-contract.yaml components/schemas (TransactionType, PaymentType, CreditCardType, transaction_mode)."""
from __future__ import annotations

from enum import Enum


class TransactionType(str, Enum):
    """Source schema: components/schemas/TransactionType."""

    Init = "Init"
    Authorize = "Authorize"
    Capture = "Capture"
    AuthorizeCapture = "AuthorizeCapture"
    Refund = "Refund"


class PaymentType(str, Enum):
    """Source schema: components/schemas/PaymentType."""

    CreditCard = "CreditCard"
    Free = "Free"
    Cod = "Cod"
    MoneyOrder = "MoneyOrder"
    Paypal = "Paypal"


class CreditCardType(str, Enum):
    """Source schema: components/schemas/CreditCardType."""

    Amex = "Amex"
    Visa = "Visa"
    Mastercard = "Mastercard"
    Diners = "Diners"
    Discovery = "Discovery"


class TransactionMode(str, Enum):
    """Source schema: inline enum on transaction_mode (SavePaymentConfigRequest / PaymentConfig)."""

    Authorize = "Authorize"
    AuthorizeCapture = "AuthorizeCapture"
