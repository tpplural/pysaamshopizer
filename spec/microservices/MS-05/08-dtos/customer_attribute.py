"""Model of MS-05 04-api-contract.yaml components/schemas/CustomerAttribute."""

from pydantic import BaseModel


class CustomerAttribute(BaseModel):
    option_id: str
    id: str | None = None
    option_value_id: str | None = None
    text_value: str | None = None
