"""FinalPrice model from MS-04 04-api-contract.yaml components/schemas/FinalPrice."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class FinalPrice(BaseModel):
    final_price: float | None = None
    original_price: float | None = None
    discounted_price: float | None = None
    default_price: bool | None = None
    discounted: bool | None = None
    discount_percent: int | None = None
    discount_end_date: datetime | None = None
