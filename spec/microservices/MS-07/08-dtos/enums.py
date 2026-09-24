"""Enums for MS-07 (tax) DTOs. Source: components/schemas.TaxBasisCalculation (04-api-contract.yaml)."""

from enum import Enum


class TaxBasisCalculation(str, Enum):
    """Configured tax basis. NOTE: not applied at runtime — billing address is always used (BR-TAX-007)."""

    StoreAddress = "StoreAddress"
    ShippingAddress = "ShippingAddress"
    BillingAddress = "BillingAddress"
