"""Model of MS-05 04-api-contract.yaml components/schemas/Customer."""

from datetime import datetime

from pydantic import BaseModel

from .address import Address
from .enums import Gender


class Customer(BaseModel):
    id: str
    store_id: str
    email_address: str
    user_name: str | None = None
    anonymous: bool | None = None
    gender: Gender | None = None
    date_of_birth: datetime | None = None
    company: str | None = None
    language: str | None = None
    billing: Address | None = None
    delivery: Address | None = None
    groups: list[int] | None = None
