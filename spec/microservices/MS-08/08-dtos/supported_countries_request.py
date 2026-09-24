"""SupportedCountriesRequest DTO. Source: 04-api-contract.yaml components/schemas/SupportedCountriesRequest."""
from pydantic import BaseModel


class SupportedCountriesRequest(BaseModel):
    items: list[str]
