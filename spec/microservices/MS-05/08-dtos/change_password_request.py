"""Model of MS-05 04-api-contract.yaml components/schemas/ChangePasswordRequest."""

from pydantic import BaseModel


class ChangePasswordRequest(BaseModel):
    current_password: str
    password: str
