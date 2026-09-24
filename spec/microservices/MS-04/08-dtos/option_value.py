"""OptionValue model from MS-04 04-api-contract.yaml components/schemas/OptionValue."""
from __future__ import annotations

from pydantic import BaseModel

from .description import Description


class OptionValue(BaseModel):
    id: str
    code: str
    display_only: bool | None = None
    descriptions: list[Description] | None = None
