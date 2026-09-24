"""SaveLandingRequest DTO. Source: components/schemas/SaveLandingRequest (04-api-contract.yaml)."""
from pydantic import BaseModel, Field

from .landing_description import LandingDescription


class SaveLandingRequest(BaseModel):
    descriptions: list[LandingDescription] = Field(min_length=1)
