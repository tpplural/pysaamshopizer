"""CreateAttributeRequest model from MS-04 04-api-contract.yaml components/schemas/CreateAttributeRequest."""
from __future__ import annotations

from pydantic import BaseModel


class CreateAttributeRequest(BaseModel):
    option_id: str
    option_value_id: str | None = None
    text_value: str | None = None
    price: str | None = None
    additional_weight: str | None = None
    sort_order: str | None = None
    default: bool | None = False
    required: bool | None = False
