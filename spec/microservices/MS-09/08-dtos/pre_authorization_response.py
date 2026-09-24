"""Pydantic v2 model for PreAuthorizationResponse. Source schema: PreAuthorizationResponse (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class PreAuthorizationResponse(BaseModel):
    """Source schema: PreAuthorizationResponse (04-api-contract.yaml)."""

    redirect_url: str | None = None
    token: str | None = None
