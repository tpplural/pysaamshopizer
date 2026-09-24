"""CreatePriceRequest model from MS-04 04-api-contract.yaml components/schemas/CreatePriceRequest."""
from __future__ import annotations

from pydantic import BaseModel

from .description_request import DescriptionRequest
from .enums import PriceType


class CreatePriceRequest(BaseModel):
    amount: str
    code: str | None = "base"
    default_price: bool | None = False
    price_type: PriceType | None = None
    special_amount: str | None = None
    special_start_date: str | None = None
    special_end_date: str | None = None
    descriptions: list[DescriptionRequest] | None = None
