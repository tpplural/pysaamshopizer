"""ShippingMethodsResponse DTO. Source: 04-api-contract.yaml components/schemas/ShippingMethodsResponse."""
from pydantic import BaseModel

from .shipping_method import ShippingMethod


class ShippingMethodsResponse(BaseModel):
    items: list[ShippingMethod] | None = None
