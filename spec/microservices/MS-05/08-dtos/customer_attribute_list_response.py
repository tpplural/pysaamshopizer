"""Model of MS-05 04-api-contract.yaml components/schemas/CustomerAttributeListResponse."""

from pydantic import BaseModel

from .customer_attribute import CustomerAttribute


class CustomerAttributeListResponse(BaseModel):
    items: list[CustomerAttribute] | None = None
