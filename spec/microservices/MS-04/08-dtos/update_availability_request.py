"""UpdateAvailabilityRequest model from MS-04 04-api-contract.yaml components/schemas/UpdateAvailabilityRequest."""
from __future__ import annotations

from pydantic import BaseModel


class UpdateAvailabilityRequest(BaseModel):
    quantity: int | None = None
    order_min: int | None = None
    order_max: int | None = None
    active: bool | None = None
