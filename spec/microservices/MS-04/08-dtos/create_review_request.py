"""CreateReviewRequest model from MS-04 04-api-contract.yaml components/schemas/CreateReviewRequest."""
from __future__ import annotations

from pydantic import BaseModel


class CreateReviewRequest(BaseModel):
    rating: int
    description: str
