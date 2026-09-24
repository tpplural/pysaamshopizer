"""Model of MS-05 04-api-contract.yaml components/schemas/Address."""

from pydantic import BaseModel


class Address(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    address: str | None = None
    city: str | None = None
    postal_code: str | None = None
    state: str | None = None
    telephone: str | None = None
    country: str | None = None
    zone: str | None = None
    billing_address: bool | None = None
