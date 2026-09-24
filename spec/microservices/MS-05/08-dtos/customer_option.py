"""Model of MS-05 04-api-contract.yaml components/schemas/CustomerOption."""

from pydantic import BaseModel

from .enums import OptionType
from .option_description import OptionDescription


class CustomerOption(BaseModel):
    id: str
    code: str
    type: OptionType | None = None
    sort_order: int | None = None
    active: bool | None = None
    public: bool | None = None
    descriptions: list[OptionDescription] | None = None
