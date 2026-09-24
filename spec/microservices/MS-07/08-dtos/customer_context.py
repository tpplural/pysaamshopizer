"""CustomerContext DTO. Source: components/schemas.CustomerContext (04-api-contract.yaml)."""

from typing import Optional

from pydantic import BaseModel

from .address import Address


class CustomerContext(BaseModel):
    billing: Optional[Address] = None
    delivery: Optional[Address] = None
