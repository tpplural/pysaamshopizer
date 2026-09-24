"""ShippingContext DTO. Source: components/schemas.ShippingContext (04-api-contract.yaml)."""

from typing import Optional

from pydantic import BaseModel


class ShippingContext(BaseModel):
    shipping: Optional[float] = None
    handling: Optional[float] = None
