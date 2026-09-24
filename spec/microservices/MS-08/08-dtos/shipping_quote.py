"""ShippingQuote DTO. Source: 04-api-contract.yaml components/schemas/ShippingQuote."""
from pydantic import BaseModel

from .enums import ShippingReturnCode
from .shipping_option import ShippingOption


class ShippingQuote(BaseModel):
    shipping_module_code: str | None = None
    options: list[ShippingOption] | None = None
    selected_option: ShippingOption | None = None
    return_code: ShippingReturnCode | None = None
    free_shipping: bool | None = None
    free_shipping_amount: float | None = None
    handling_fees: float | None = None
    apply_tax_on_shipping: bool | None = None
    quote_error: str | None = None
