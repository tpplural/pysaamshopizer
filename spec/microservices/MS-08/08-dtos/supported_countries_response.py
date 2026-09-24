"""SupportedCountriesResponse DTO. Source: 04-api-contract.yaml components/schemas/SupportedCountriesResponse."""
from pydantic import BaseModel


class SupportedCountriesResponse(BaseModel):
    items: list[str] | None = None
