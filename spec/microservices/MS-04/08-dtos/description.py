"""Description model from MS-04 04-api-contract.yaml components/schemas/Description."""
from __future__ import annotations

from pydantic import BaseModel


class Description(BaseModel):
    language_code: str
    name: str
    id: str | None = None
    description: str | None = None
