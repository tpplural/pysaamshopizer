"""CreateRelationshipRequest model from MS-04 04-api-contract.yaml components/schemas/CreateRelationshipRequest."""
from __future__ import annotations

from pydantic import BaseModel


class CreateRelationshipRequest(BaseModel):
    group_code: str
    related_product_id: str | None = None
    active: bool | None = True
