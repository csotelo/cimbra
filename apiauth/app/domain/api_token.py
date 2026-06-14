"""APIToken entity."""

from datetime import datetime

from pydantic import BaseModel


class APIToken(BaseModel):
    """Read-only API token entity from PostgreSQL.

    This entity represents token data fetched from Django's api_tokens table.
    FastAPI only reads - no mutations allowed.
    """

    id: str
    token: str
    tenant_id: str
    owner_id: str
    is_active: bool
    expires_at: datetime
    last_used_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
