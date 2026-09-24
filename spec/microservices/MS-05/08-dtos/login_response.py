"""Model of MS-05 04-api-contract.yaml components/schemas/LoginResponse."""

from pydantic import BaseModel


class LoginResponse(BaseModel):
    status: str | None = None
    authenticated: bool | None = None
    cart_code: str | None = None
    authorities: list[str] | None = None
