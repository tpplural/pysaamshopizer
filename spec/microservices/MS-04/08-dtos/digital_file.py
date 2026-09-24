"""DigitalFile model from MS-04 04-api-contract.yaml components/schemas/DigitalFile."""
from __future__ import annotations

from pydantic import BaseModel


class DigitalFile(BaseModel):
    product_id: str | None = None
    file_name: str | None = None
    virtual: bool | None = None
