"""Model of MS-05 04-api-contract.yaml components/schemas/CreateCustomerOptionSetRequest."""

from pydantic import BaseModel


class CreateCustomerOptionSetRequest(BaseModel):
    option_id: str
    option_value_id: str
    sort_order: int | None = None
