"""Pydantic v2 model for OrderProductDownload. Source schema: OrderProductDownload (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel


class OrderProductDownload(BaseModel):
    """Source schema: OrderProductDownload (04-api-contract.yaml)."""

    download_id: str | None = None
    filename: str | None = None
    max_days: int | None = None
    download_count: int | None = None
