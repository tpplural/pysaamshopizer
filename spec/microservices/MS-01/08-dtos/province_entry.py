"""Response DTO. Source schema: components/schemas.ProvinceEntry."""

from __future__ import annotations

from pydantic import BaseModel


class ProvinceEntry(BaseModel):
    name: str
    code: str
    id: int
