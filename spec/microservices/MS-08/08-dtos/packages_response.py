"""PackagesResponse DTO. Source: 04-api-contract.yaml components/schemas/PackagesResponse."""
from pydantic import BaseModel

from .package_detail import PackageDetail


class PackagesResponse(BaseModel):
    items: list[PackageDetail] | None = None
