"""Review model from MS-04 04-api-contract.yaml components/schemas/Review."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class Review(BaseModel):
    id: str
    rating: int | None = None
    description: str | None = None
    date: date | None = None
    product_review_avg: float | None = None
    product_review_count: int | None = None
