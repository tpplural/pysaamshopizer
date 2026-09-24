"""CodeAvailabilityResponse DTO. Source: components/schemas/CodeAvailabilityResponse (04-api-contract.yaml)."""
from pydantic import BaseModel


class CodeAvailabilityResponse(BaseModel):
    code: str
    available: bool
