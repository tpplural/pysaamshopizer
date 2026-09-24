"""Model of MS-05 04-api-contract.yaml components/schemas/CreateCustomerOptionValueRequest."""

from pydantic import BaseModel

from .option_description import OptionDescription


class CreateCustomerOptionValueRequest(BaseModel):
    code: str
    descriptions: list[OptionDescription]
    sort_order: int | None = None
    image: str | None = None
