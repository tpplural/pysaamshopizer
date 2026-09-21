"""Response DTO. Source schema: components/schemas.LanguageListResponse."""

from __future__ import annotations

from pydantic import BaseModel

from .language import Language


class LanguageListResponse(BaseModel):
    items: list[Language]
