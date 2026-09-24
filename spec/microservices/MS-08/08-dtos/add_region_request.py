"""AddRegionRequest DTO. Source: 04-api-contract.yaml components/schemas/AddRegionRequest."""
from pydantic import BaseModel


class AddRegionRequest(BaseModel):
    custom_region_name: str
