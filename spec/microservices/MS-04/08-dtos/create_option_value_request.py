"""CreateOptionValueRequest model from MS-04 04-api-contract.yaml components/schemas/CreateOptionValueRequest."""
from __future__ import annotations

from pydantic import BaseModel

from .description_request import DescriptionRequest


class CreateOptionValueRequest(BaseModel):
    code: str
    descriptions: list[DescriptionRequest]
