"""SaveShippingProviderRequest DTO. Source: 04-api-contract.yaml components/schemas/SaveShippingProviderRequest."""
from pydantic import BaseModel


class SaveShippingProviderRequest(BaseModel):
    module_code: str
    active: bool | None = None
