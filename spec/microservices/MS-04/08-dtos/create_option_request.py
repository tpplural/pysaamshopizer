"""CreateOptionRequest model from MS-04 04-api-contract.yaml components/schemas/CreateOptionRequest."""
from __future__ import annotations

from pydantic import BaseModel

from .description_request import DescriptionRequest
from .enums import OptionWidgetType


class CreateOptionRequest(BaseModel):
    code: str
    type: OptionWidgetType | None = None
    read_only: bool | None = False
    descriptions: list[DescriptionRequest] | None = None
