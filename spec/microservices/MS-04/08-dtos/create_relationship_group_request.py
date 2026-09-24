"""CreateRelationshipGroupRequest model from MS-04 04-api-contract.yaml components/schemas/CreateRelationshipGroupRequest."""
from __future__ import annotations

from pydantic import BaseModel


class CreateRelationshipGroupRequest(BaseModel):
    code: str
