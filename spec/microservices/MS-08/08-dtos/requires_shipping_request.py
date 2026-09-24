"""RequiresShippingRequest DTO. Source: 04-api-contract.yaml components/schemas/RequiresShippingRequest."""
from pydantic import BaseModel

from .shipping_item import ShippingItem


class RequiresShippingRequest(BaseModel):
    items: list[ShippingItem]
