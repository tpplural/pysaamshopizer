"""CustomWeightConfiguration DTO. Source: 04-api-contract.yaml components/schemas/CustomWeightConfiguration."""
from pydantic import BaseModel

from .custom_weight_region import CustomWeightRegion


class CustomWeightConfiguration(BaseModel):
    module_code: str | None = None
    active: bool | None = None
    regions: list[CustomWeightRegion] | None = None
