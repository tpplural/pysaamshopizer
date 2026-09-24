"""Pydantic v2 model for OrderDownloadList. Source schema: OrderDownloadList (04-api-contract.yaml)."""

from __future__ import annotations

from pydantic import BaseModel

from .order_product_download import OrderProductDownload


class OrderDownloadList(BaseModel):
    """Source schema: OrderDownloadList (04-api-contract.yaml)."""

    has_downloads: bool | None = None
    downloads: list[OrderProductDownload] | None = None


OrderDownloadList.model_rebuild()
