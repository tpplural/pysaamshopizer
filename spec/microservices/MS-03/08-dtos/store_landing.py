"""StoreLanding DTO. Source: components/schemas/StoreLanding (04-api-contract.yaml)."""
from pydantic import BaseModel

from .landing_description import LandingDescription


class StoreLanding(BaseModel):
    code: str
    landing_code: str
    provisioned: bool | None = None
    descriptions: list[LandingDescription] | None = None
