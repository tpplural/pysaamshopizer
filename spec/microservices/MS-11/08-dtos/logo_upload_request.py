"""LogoUploadRequest DTO (multipart/form-data). Source: 04-api-contract.yaml #/components/schemas/LogoUploadRequest."""
from pydantic import BaseModel


class LogoUploadRequest(BaseModel):
    file: bytes
