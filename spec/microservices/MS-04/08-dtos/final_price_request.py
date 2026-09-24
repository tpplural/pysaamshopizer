"""FinalPriceRequest model from MS-04 04-api-contract.yaml components/schemas/FinalPriceRequest."""
from __future__ import annotations

from pydantic import BaseModel


class FinalPriceRequest(BaseModel):
    selected_attribute_ids: list[str] | None = None
