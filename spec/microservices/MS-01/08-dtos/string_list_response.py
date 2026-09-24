"""Response DTO. Source schema: components/schemas.StringListResponse."""

from __future__ import annotations

from pydantic import BaseModel


class StringListResponse(BaseModel):
    items: list[str]
