"""ShippingSummary DTO. Source: 04-api-contract.yaml components/schemas/ShippingSummary."""
from pydantic import BaseModel


class ShippingSummary(BaseModel):
    shipping: float | None = None
    handling: float | None = None
    shipping_module: str | None = None
    shipping_option: str | None = None
    free_shipping: bool | None = None
    tax_on_shipping: bool | None = None
