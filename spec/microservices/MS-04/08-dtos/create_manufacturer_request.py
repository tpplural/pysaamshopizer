"""CreateManufacturerRequest model from MS-04 04-api-contract.yaml components/schemas/CreateManufacturerRequest."""
from __future__ import annotations

from pydantic import BaseModel

from .description_request import DescriptionRequest


class CreateManufacturerRequest(BaseModel):
    code: str
    descriptions: list[DescriptionRequest]
    sort_order: int | None = 0
