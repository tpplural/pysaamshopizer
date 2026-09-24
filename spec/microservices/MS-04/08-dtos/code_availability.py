"""CodeAvailability model from MS-04 04-api-contract.yaml components/schemas/CodeAvailability."""
from __future__ import annotations

from pydantic import BaseModel


class CodeAvailability(BaseModel):
    available: bool | None = None
    reason: str | None = None
