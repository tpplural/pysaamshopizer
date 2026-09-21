"""Response DTO. Source schema: components/schemas.ZoneListResponse."""

from __future__ import annotations

from pydantic import BaseModel

from .zone import Zone


class ZoneListResponse(BaseModel):
    items: list[Zone]
