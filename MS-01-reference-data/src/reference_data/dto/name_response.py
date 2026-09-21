"""Response DTO. Source schema: components/schemas.NameResponse."""

from __future__ import annotations

from pydantic import BaseModel, Field


class NameResponse(BaseModel):
    value: str = Field(
        ...,
        description="Localized name, or the echoed input code if unresolved (BR-REF-API-002)",
    )
