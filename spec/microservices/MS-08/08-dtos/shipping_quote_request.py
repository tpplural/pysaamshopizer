"""ShippingQuoteRequest DTO. Source: 04-api-contract.yaml components/schemas/ShippingQuoteRequest."""
from pydantic import BaseModel

from .delivery import Delivery
from .shipping_item import ShippingItem


class ShippingQuoteRequest(BaseModel):
    delivery: Delivery
    items: list[ShippingItem]
    language_code: str | None = None
