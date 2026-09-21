"""Response DTO. Source schema: components/schemas.ProvincesResponse (fail-soft envelope, BR-REF-API-001)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .enums import ProvincesStatus
from .province_entry import ProvinceEntry


class ProvincesResponse(BaseModel):
    status: ProvincesStatus = Field(..., description="Fail-soft status (BR-REF-API-001)")
    items: list[ProvinceEntry]
