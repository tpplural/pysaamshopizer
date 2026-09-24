"""SavePaymentConfigRequest DTO. Source schema: components/schemas/SavePaymentConfigRequest (04-api-contract.yaml)."""
from __future__ import annotations

from pydantic import BaseModel

from .enums import TransactionMode


class SavePaymentConfigRequest(BaseModel):
    active: bool
    default_selected: bool | None = None
    transaction_mode: TransactionMode | None = None
    integration_keys: dict[str, str] | None = None
