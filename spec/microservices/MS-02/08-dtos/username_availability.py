"""UsernameAvailability DTO — source: components/schemas/UsernameAvailability (04-api-contract.yaml)."""

from pydantic import BaseModel


class UsernameAvailability(BaseModel):
    available: bool
    reason: str | None = None
