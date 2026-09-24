"""Model of MS-05 04-api-contract.yaml components/schemas/AvailableOption."""

from pydantic import BaseModel

from .enums import OptionType


class AvailableOption(BaseModel):
    id: str | None = None
    code: str | None = None
    type: OptionType | None = None
    name: str | None = None
    active: bool | None = None
    public: bool | None = None
    selected_value_id: str | None = None
    selected_text: str | None = None
