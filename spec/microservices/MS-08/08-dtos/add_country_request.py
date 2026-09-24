"""AddCountryRequest DTO. Source: 04-api-contract.yaml components/schemas/AddCountryRequest."""
from pydantic import BaseModel


class AddCountryRequest(BaseModel):
    country_code: str
