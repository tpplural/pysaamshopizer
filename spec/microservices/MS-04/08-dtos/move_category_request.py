"""MoveCategoryRequest model from MS-04 04-api-contract.yaml components/schemas/MoveCategoryRequest."""
from __future__ import annotations

from pydantic import BaseModel


class MoveCategoryRequest(BaseModel):
    parent_id: int
