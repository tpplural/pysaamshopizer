"""Enums for reference-data (MS-01) DTOs. Source: components/schemas.ProvincesResponse.status."""

from enum import Enum


class ProvincesStatus(str, Enum):
    """Fail-soft status enum (BR-REF-API-001). Source: ProvincesResponse.status."""

    Success = "Success"
    Failure = "Failure"
