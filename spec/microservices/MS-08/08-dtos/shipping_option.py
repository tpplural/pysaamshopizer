"""ShippingOption DTO. Source: 04-api-contract.yaml components/schemas/ShippingOption."""
from pydantic import BaseModel


class ShippingOption(BaseModel):
    option_id: str | None = None
    option_code: str | None = None
    option_name: str | None = None
    option_price: float | None = None
    option_price_text: str | None = None
    description: str | None = None
