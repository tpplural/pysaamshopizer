"""DescriptionRequest model from MS-04 04-api-contract.yaml components/schemas/DescriptionRequest."""
from __future__ import annotations

from pydantic import BaseModel


class DescriptionRequest(BaseModel):
    language_code: str
    name: str
    description: str | None = None
