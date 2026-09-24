"""LoginResponse DTO — source: components/schemas/LoginResponse (04-api-contract.yaml)."""

from pydantic import BaseModel


class LoginResponse(BaseModel):
    authenticated: bool
    user_id: int | None = None
    authorities: list[str] | None = None
    last_access: str | None = None
    login_time: str | None = None
