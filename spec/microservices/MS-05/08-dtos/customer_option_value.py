"""Model of MS-05 04-api-contract.yaml components/schemas/CustomerOptionValue."""

from pydantic import BaseModel

from .option_description import OptionDescription


class CustomerOptionValue(BaseModel):
    id: str
    code: str
    sort_order: int | None = None
    image: str | None = None
    descriptions: list[OptionDescription] | None = None
