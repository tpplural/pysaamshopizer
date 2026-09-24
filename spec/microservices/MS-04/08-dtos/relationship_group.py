"""RelationshipGroup model from MS-04 04-api-contract.yaml components/schemas/RelationshipGroup."""
from __future__ import annotations

from pydantic import BaseModel


class RelationshipGroup(BaseModel):
    code: str | None = None
    active: bool | None = None
