"""SaveShippingPackagingRequest DTO. Source: 04-api-contract.yaml components/schemas/SaveShippingPackagingRequest."""
from pydantic import BaseModel

from .enums import ShippingPackageType


class SaveShippingPackagingRequest(BaseModel):
    box_width: int | None = None
    box_height: int | None = None
    box_length: int | None = None
    box_weight: float | None = None
    shipping_package_type: ShippingPackageType
