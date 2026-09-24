"""LoginRequest DTO — source: components/schemas/LoginRequest (04-api-contract.yaml)."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str
