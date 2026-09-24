"""CreateAvailabilityRequest model from MS-04 04-api-contract.yaml components/schemas/CreateAvailabilityRequest."""
from __future__ import annotations

from pydantic import BaseModel


class CreateAvailabilityRequest(BaseModel):
    region: str | None = "*"
    quantity: int | None = 0
    order_min: int | None = 0
    order_max: int | None = 0
