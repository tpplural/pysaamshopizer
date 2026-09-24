"""ImageUploadRequest model from MS-04 04-api-contract.yaml components/schemas/ImageUploadRequest."""
from __future__ import annotations

from pydantic import BaseModel


class ImageUploadRequest(BaseModel):
    content: str
    file_name: str | None = None
