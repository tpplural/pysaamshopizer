"""FileUploadRequest DTO (multipart/form-data). Source: 04-api-contract.yaml #/components/schemas/FileUploadRequest."""
from pydantic import BaseModel

from .enums import FileContentType


class FileUploadRequest(BaseModel):
    file_type: FileContentType | None = None
    files: list[bytes]
