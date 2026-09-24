"""SaveShippingOptionsRequest DTO. Source: 04-api-contract.yaml components/schemas/SaveShippingOptionsRequest."""
from pydantic import BaseModel

from .enums import ShippingOptionPriceType, ShippingType


class SaveShippingOptionsRequest(BaseModel):
    free_shipping_enabled: bool | None = None
    order_total_free_shipping_text: str | None = None
    handling_fees_text: str | None = None
    tax_on_shipping: bool | None = None
    free_shipping_type: ShippingType | None = None
    shipping_option_price_type: ShippingOptionPriceType | None = None
