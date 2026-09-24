"""UploadImagesRequest model from MS-04 04-api-contract.yaml components/schemas/UploadImagesRequest (inline items object modeled as UploadImageItem)."""
from __future__ import annotations

from pydantic import BaseModel


class UploadImageItem(BaseModel):
    content: str | None = None
    file_name: str | None = None


class UploadImagesRequest(BaseModel):
    images: list[UploadImageItem]
