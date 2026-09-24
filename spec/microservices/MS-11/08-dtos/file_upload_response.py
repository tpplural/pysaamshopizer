"""FileUploadResponse DTO. Source: 04-api-contract.yaml #/components/schemas/FileUploadResponse."""
from pydantic import BaseModel

from .enums import FileContentType


class FileUploadResponse(BaseModel):
    stored: list[str] | None = None
    file_type: FileContentType | None = None
