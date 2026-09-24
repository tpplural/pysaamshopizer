"""OptionType model from MS-04 04-api-contract.yaml components/schemas/OptionType."""
from __future__ import annotations

from pydantic import BaseModel

from .enums import OptionWidgetType


class OptionType(BaseModel):
    type: OptionWidgetType | None = None
