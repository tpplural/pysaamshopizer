"""AuthorizationDecision DTO — source: components/schemas/AuthorizationDecision (04-api-contract.yaml)."""

from pydantic import BaseModel


class AuthorizationDecision(BaseModel):
    role: str
    granted: bool
