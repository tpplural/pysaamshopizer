"""Model of MS-05 04-api-contract.yaml components/schemas/CustomerOptionSet."""

from pydantic import BaseModel


class CustomerOptionSet(BaseModel):
    id: str
    option_id: str
    option_value_id: str
    sort_order: int | None = None
