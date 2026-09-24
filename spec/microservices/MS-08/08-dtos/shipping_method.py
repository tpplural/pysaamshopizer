"""ShippingMethod DTO. Source: 04-api-contract.yaml components/schemas/ShippingMethod."""
from pydantic import BaseModel


class ShippingMethod(BaseModel):
    code: str | None = None
    regions: list[str] | None = None
