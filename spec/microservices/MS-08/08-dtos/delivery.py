"""Delivery DTO. Source: 04-api-contract.yaml components/schemas/Delivery."""
from pydantic import BaseModel


class Delivery(BaseModel):
    country_code: str
    name: str | None = None
