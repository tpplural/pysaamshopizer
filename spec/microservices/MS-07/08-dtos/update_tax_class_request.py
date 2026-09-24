"""UpdateTaxClassRequest DTO. Source: components/schemas.UpdateTaxClassRequest (04-api-contract.yaml)."""

from pydantic import BaseModel, Field


class UpdateTaxClassRequest(BaseModel):
    code: str = Field(max_length=10)
    title: str = Field(max_length=32)
