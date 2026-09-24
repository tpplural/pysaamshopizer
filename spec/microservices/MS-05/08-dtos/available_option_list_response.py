"""Model of MS-05 04-api-contract.yaml components/schemas/AvailableOptionListResponse."""

from pydantic import BaseModel

from .available_option import AvailableOption


class AvailableOptionListResponse(BaseModel):
    items: list[AvailableOption] | None = None
