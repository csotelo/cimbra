"""Tenant entity."""

from datetime import datetime

from pydantic import BaseModel, Field


class Tenant(BaseModel):
    """Read-only tenant entity from PostgreSQL.

    This entity represents tenant data fetched from Django's tenants table.
    FastAPI only reads - no mutations allowed.
    """

    id: str
    name: str
    slug: str
    is_active: bool
    max_users: int
    rate_limit: int = Field(default=60, description="requests per minute")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
