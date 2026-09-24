"""ShippingProvider DTO. Source: 04-api-contract.yaml components/schemas/ShippingProvider."""
from pydantic import BaseModel


class ShippingProvider(BaseModel):
    module_code: str | None = None
    active: bool | None = None
