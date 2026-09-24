"""AddWeightBracketRequest DTO. Source: 04-api-contract.yaml components/schemas/AddWeightBracketRequest."""
from pydantic import BaseModel


class AddWeightBracketRequest(BaseModel):
    maximum_weight: int
    price_text: str
