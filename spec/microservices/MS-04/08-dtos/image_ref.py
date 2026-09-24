"""ImageRef model from MS-04 04-api-contract.yaml components/schemas/ImageRef."""
from __future__ import annotations

from pydantic import BaseModel


class ImageRef(BaseModel):
    id: str | None = None
    name: str | None = None
    url: str | None = None
