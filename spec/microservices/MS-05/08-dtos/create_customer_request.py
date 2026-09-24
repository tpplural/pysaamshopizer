"""Model of MS-05 04-api-contract.yaml components/schemas/CreateCustomerRequest."""

from pydantic import BaseModel

from .address import Address
from .enums import Gender


class CreateCustomerRequest(BaseModel):
    email_address: str
    user_name: str | None = None
    password: str | None = None
    gender: Gender | None = None
    language: str | None = None
    company: str | None = None
    billing: Address | None = None
    delivery: Address | None = None
