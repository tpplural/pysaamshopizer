"""Product model from MS-04 04-api-contract.yaml components/schemas/Product."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from .availability import Availability
from .description import Description


class Product(BaseModel):
    id: str
    sku: str
    available: bool | None = None
    date_available: datetime | None = None
    visible: bool | None = None
    virtual: bool | None = None
    shippable: bool | None = None
    free: bool | None = None
    sort_order: int | None = None
    manufacturer_id: str | None = None
    type_code: str | None = None
    product_review_avg: float | None = None
    product_review_count: int | None = None
    descriptions: list[Description] | None = None
    availabilities: list[Availability] | None = None
