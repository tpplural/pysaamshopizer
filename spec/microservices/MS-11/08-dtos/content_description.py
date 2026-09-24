"""ContentDescription DTO. Source: 04-api-contract.yaml #/components/schemas/ContentDescription."""
from pydantic import BaseModel, Field


class ContentDescription(BaseModel):
    language_code: str
    name: str = Field(max_length=120)
    title: str | None = None
    body: str | None = None
    friendly_url: str | None = Field(default=None, max_length=120)
    meta_title: str | None = None
    meta_keywords: str | None = None
    meta_description: str | None = None
