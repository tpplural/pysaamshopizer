"""Model of MS-05 04-api-contract.yaml components/schemas/CreateCustomerOptionRequest."""

from pydantic import BaseModel

from .enums import OptionType
from .option_description import OptionDescription


class CreateCustomerOptionRequest(BaseModel):
    code: str
    descriptions: list[OptionDescription]
    type: OptionType | None = None
    sort_order: int | None = None
    active: bool | None = None
    public: bool | None = None
