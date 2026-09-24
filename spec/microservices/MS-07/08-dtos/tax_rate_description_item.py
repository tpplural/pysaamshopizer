"""TaxRateDescriptionItem DTO. Source: components/schemas.TaxRateDescriptionItem (04-api-contract.yaml)."""

from pydantic import BaseModel, Field


class TaxRateDescriptionItem(BaseModel):
    language_id: int
    name: str = Field(max_length=120)
