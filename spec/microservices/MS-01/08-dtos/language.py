"""Response DTO. Source schema: components/schemas.Language."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Language(BaseModel):
    code: str = Field(..., description="Language code, e.g. en/fr (BR-REF-RES-002)")
    sort_order: int | None = Field(
        default=None, description="Display order (unset at seed in legacy — NF-4)"
    )
