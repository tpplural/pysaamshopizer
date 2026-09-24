"""CodeAvailabilityResponse DTO. Source: 04-api-contract.yaml #/components/schemas/CodeAvailabilityResponse."""
from pydantic import BaseModel


class CodeAvailabilityResponse(BaseModel):
    code: str
    available: bool
    reason: str | None = None
