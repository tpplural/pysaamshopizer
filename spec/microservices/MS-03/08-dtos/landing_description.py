"""LandingDescription DTO. Source: components/schemas/LandingDescription (04-api-contract.yaml)."""
from pydantic import BaseModel


class LandingDescription(BaseModel):
    language_code: str
    title: str
    home_page_content: str | None = None
    keywords: str | None = None
    description: str | None = None
