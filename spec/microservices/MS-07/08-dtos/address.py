"""Address DTO. Source: components/schemas.Address (04-api-contract.yaml)."""

from typing import Optional

from pydantic import BaseModel


class Address(BaseModel):
    country_id: Optional[int] = None
    zone_id: Optional[int] = None
    state: Optional[str] = None
