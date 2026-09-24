"""StoreContext DTO. Source: components/schemas.StoreContext (04-api-contract.yaml)."""

from typing import Optional

from pydantic import BaseModel


class StoreContext(BaseModel):
    country_id: Optional[int] = None
    zone_id: Optional[int] = None
    state_province: Optional[str] = None
