"""Model of MS-05 04-api-contract.yaml components/schemas/OptionDescription."""

from pydantic import BaseModel


class OptionDescription(BaseModel):
    language: str
    name: str
