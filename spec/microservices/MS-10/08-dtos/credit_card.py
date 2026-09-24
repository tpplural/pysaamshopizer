"""CreditCard DTO. Source schema: components/schemas/CreditCard (04-api-contract.yaml)."""
from __future__ import annotations

from pydantic import BaseModel

from .enums import CreditCardType


class CreditCard(BaseModel):
    number: str
    type: CreditCardType
    exp_month: str
    exp_year: str
    card_owner: str | None = None
