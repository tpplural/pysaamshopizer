"""Model of MS-05 04-api-contract.yaml components/schemas/UpdateCustomerRequest."""

from pydantic import BaseModel

from .address import Address
from .enums import Gender


class UpdateCustomerRequest(BaseModel):
    email_address: str | None = None
    gender: Gender | None = None
    company: str | None = None
    language: str | None = None
    billing: Address | None = None
    delivery: Address | None = None
