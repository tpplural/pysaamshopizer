"""Price model from MS-04 04-api-contract.yaml components/schemas/Price."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from .enums import PriceType


class Price(BaseModel):
    id: str | None = None
    code: str | None = None
    default_price: bool | None = None
    price_type: PriceType | None = None
    amount: float | None = None
    special_amount: float | None = None
    special_start_date: datetime | None = None
    special_end_date: datetime | None = None
    has_discount: bool | None = None
