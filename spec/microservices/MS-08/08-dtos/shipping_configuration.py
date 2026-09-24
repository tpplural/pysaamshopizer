"""ShippingConfiguration DTO. Source: 04-api-contract.yaml components/schemas/ShippingConfiguration."""
from pydantic import BaseModel

from .enums import (
    ShippingBasisType,
    ShippingOptionPriceType,
    ShippingPackageType,
    ShippingType,
)


class ShippingConfiguration(BaseModel):
    shipping_type: ShippingType | None = None
    shipping_basis_type: ShippingBasisType | None = None
    shipping_option_price_type: ShippingOptionPriceType | None = None
    shipping_package_type: ShippingPackageType | None = None
    free_shipping_type: ShippingType | None = None
    box_width: int | None = None
    box_height: int | None = None
    box_length: int | None = None
    box_weight: float | None = None
    max_weight: float | None = None
    free_shipping_enabled: bool | None = None
    order_total_free_shipping: float | None = None
    handling_fees: float | None = None
    tax_on_shipping: bool | None = None
