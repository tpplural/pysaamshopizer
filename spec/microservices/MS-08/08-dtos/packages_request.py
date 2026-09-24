"""PackagesRequest DTO. Source: 04-api-contract.yaml components/schemas/PackagesRequest."""
from pydantic import BaseModel

from .enums import ShippingPackageType
from .shipping_item import ShippingItem


class PackagesRequest(BaseModel):
    strategy: ShippingPackageType | None = None
    items: list[ShippingItem]
