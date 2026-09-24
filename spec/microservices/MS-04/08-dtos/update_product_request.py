"""UpdateProductRequest model from MS-04 04-api-contract.yaml components/schemas/UpdateProductRequest."""
from __future__ import annotations

from pydantic import BaseModel

from .availability import Availability
from .description_request import DescriptionRequest


class UpdateProductRequest(BaseModel):
    sku: str | None = None
    type_code: str | None = None
    manufacturer_id: str | None = None
    available: bool | None = None
    descriptions: list[DescriptionRequest] | None = None
    availabilities: list[Availability] | None = None
