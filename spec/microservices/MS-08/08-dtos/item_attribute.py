"""ItemAttribute DTO. Source: 04-api-contract.yaml components/schemas/ItemAttribute."""
from pydantic import BaseModel


class ItemAttribute(BaseModel):
    additional_weight: float | None = None
