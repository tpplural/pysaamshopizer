"""Enums for MS-02 identity-admin — source: components/schemas.GroupType (04-api-contract.yaml)."""

from enum import Enum


class GroupType(str, Enum):
    """Group classification (BR-SC-RBAC-004). Wire values map to legacy ADMIN|CUSTOMER."""

    Admin = "Admin"
    Customer = "Customer"
