"""CreateProductRequest model from MS-04 04-api-contract.yaml components/schemas/CreateProductRequest."""
from __future__ import annotations

from pydantic import BaseModel

from .create_availability_request import CreateAvailabilityRequest
from .description_request import DescriptionRequest


class CreateProductRequest(BaseModel):
    sku: str
    availabilities: list[CreateAvailabilityRequest]
    type_code: str | None = None
    manufacturer_id: str | None = None
    available: bool | None = True
    price: str | None = None
    descriptions: list[DescriptionRequest] | None = None
