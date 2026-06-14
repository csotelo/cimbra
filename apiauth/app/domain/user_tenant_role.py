"""UserTenantRole entity."""

from pydantic import BaseModel


class UserTenantRole(BaseModel):
    """Read-only user-tenant role entity from PostgreSQL.

    This entity represents the M2M relationship between users and tenants.
    Roles: OWNER=owner, ADMIN=admin, MEMBER=member
    """

    class Role:
        OWNER = "owner"
        ADMIN = "admin"
        MEMBER = "member"

    user_id: str
    tenant_id: str
    role: str

    class Config:
        from_attributes = True
