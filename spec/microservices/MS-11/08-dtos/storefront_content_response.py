"""StorefrontContentResponse DTO. Source: 04-api-contract.yaml #/components/schemas/StorefrontContentResponse."""
from pydantic import BaseModel


class StorefrontContentResponse(BaseModel):
    code: str | None = None
    view: str | None = None
    name: str | None = None
    body: str | None = None
    meta_title: str | None = None
    meta_keywords: str | None = None
    meta_description: str | None = None
    friendly_url: str | None = None
