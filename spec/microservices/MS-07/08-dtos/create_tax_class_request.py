"""CreateTaxClassRequest DTO. Source: components/schemas.CreateTaxClassRequest (04-api-contract.yaml)."""

from pydantic import BaseModel, Field


class CreateTaxClassRequest(BaseModel):
    code: str = Field(max_length=10)
    title: str = Field(max_length=32)
