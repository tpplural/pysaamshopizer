"""StoreBranding DTO. Source: components/schemas/StoreBranding (04-api-contract.yaml)."""
from pydantic import BaseModel, Field


class StoreBranding(BaseModel):
    code: str
    store_logo: str | None = Field(default=None, max_length=100)
    store_template: str | None = Field(default=None, max_length=25)
