"""Pydantic v2 model for ValidationResult. Source schema: ValidationResult (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class ValidationResult(BaseModel):
    """Source schema: ValidationResult (04-api-contract.yaml)."""

    valid: bool
    messages: list[str] | None = None
