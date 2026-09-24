"""CustomWeightRegion DTO. Source: 04-api-contract.yaml components/schemas/CustomWeightRegion."""
from pydantic import BaseModel

from .custom_weight_bracket import CustomWeightBracket


class CustomWeightRegion(BaseModel):
    custom_region_name: str
    countries: list[str] | None = None
    quote_items: list[CustomWeightBracket] | None = None
