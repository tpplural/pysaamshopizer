"""SaveShippingModeRequest DTO. Source: 04-api-contract.yaml components/schemas/SaveShippingModeRequest."""
from pydantic import BaseModel

from .enums import ShippingType


class SaveShippingModeRequest(BaseModel):
    shipping_type: ShippingType
