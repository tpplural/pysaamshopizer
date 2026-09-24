"""Local model of shared common-schemas.yaml#/components/schemas/ErrorResponse (referenced by MS-02 error responses)."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int
    timestamp: str | None = None
