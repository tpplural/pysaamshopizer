"""SetTemplateRequest DTO. Source: components/schemas/SetTemplateRequest (04-api-contract.yaml)."""
from pydantic import BaseModel, Field


class SetTemplateRequest(BaseModel):
    template: str = Field(max_length=25)
