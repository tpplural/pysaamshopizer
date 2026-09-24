"""RequiresShippingResponse DTO. Source: 04-api-contract.yaml components/schemas/RequiresShippingResponse."""
from pydantic import BaseModel


class RequiresShippingResponse(BaseModel):
    requires_shipping: bool | None = None
