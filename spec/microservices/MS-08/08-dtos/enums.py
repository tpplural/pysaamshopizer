"""Enums for MS-08 shipping DTOs. Source: 04-api-contract.yaml components/schemas (enum types)."""
from enum import Enum


class ShippingType(str, Enum):
    National = "National"
    International = "International"


class ShippingBasisType(str, Enum):
    Billing = "Billing"
    Shipping = "Shipping"


class ShippingOptionPriceType(str, Enum):
    Least = "Least"
    Highest = "Highest"
    All = "All"


class ShippingPackageType(str, Enum):
    Item = "Item"
    Box = "Box"


class ShippingReturnCode(str, Enum):
    # External/legacy status codes — kept UPPER_CASE per contract (Concern G note).
    NO_SHIPPING_TO_SELECTED_COUNTRY = "NO_SHIPPING_TO_SELECTED_COUNTRY"
    NO_SHIPPING_MODULE_CONFIGURED = "NO_SHIPPING_MODULE_CONFIGURED"
    ERROR = "ERROR"
