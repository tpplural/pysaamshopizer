"""CustomWeightBracket DTO. Source: 04-api-contract.yaml components/schemas/CustomWeightBracket."""
from pydantic import BaseModel


class CustomWeightBracket(BaseModel):
    maximum_weight: int
    price: float
    price_text: str | None = None
