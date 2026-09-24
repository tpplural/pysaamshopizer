"""Model of MS-05 04-api-contract.yaml components/schemas/RegisterCustomerRequest."""

from pydantic import BaseModel

from .address import Address
from .enums import Gender


class RegisterCustomerRequest(BaseModel):
    user_name: str
    password: str
    check_password: str
    email_address: str
    gender: Gender | None = None
    language: str | None = None
    billing: Address | None = None
    delivery: Address | None = None
    captcha_challenge: str | None = None
    captcha_response: str | None = None
