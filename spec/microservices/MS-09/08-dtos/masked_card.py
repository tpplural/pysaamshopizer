"""Pydantic v2 model for MaskedCard. Source schema: MaskedCard (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class MaskedCard(BaseModel):
    """Source schema: MaskedCard (04-api-contract.yaml)."""

    masked_number: str | None = None
    card_type: str | None = None
    holder: str | None = None
    expires: str | None = None
