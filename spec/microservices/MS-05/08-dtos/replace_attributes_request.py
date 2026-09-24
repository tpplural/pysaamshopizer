"""Model of MS-05 04-api-contract.yaml components/schemas/ReplaceAttributesRequest."""

from pydantic import BaseModel

from .customer_attribute import CustomerAttribute


class ReplaceAttributesRequest(BaseModel):
    attributes: list[CustomerAttribute]
