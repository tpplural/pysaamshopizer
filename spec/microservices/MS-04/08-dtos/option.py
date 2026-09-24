"""Option model from MS-04 04-api-contract.yaml components/schemas/Option."""
from __future__ import annotations

from pydantic import BaseModel

from .description import Description
from .enums import OptionWidgetType


class Option(BaseModel):
    id: str
    code: str
    type: OptionWidgetType | None = None
    read_only: bool | None = None
    descriptions: list[Description] | None = None
