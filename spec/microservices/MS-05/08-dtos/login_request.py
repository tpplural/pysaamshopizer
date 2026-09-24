"""Model of MS-05 04-api-contract.yaml components/schemas/LoginRequest."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    user_name: str
    password: str
    session_cart_code: str | None = None
