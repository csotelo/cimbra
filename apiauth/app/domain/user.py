"""CustomUser entity."""

from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    """Read-only user entity from PostgreSQL.

    This entity represents user data fetched from Django's custom_users table.
    FastAPI only reads - no mutations allowed.
    """

    id: str
    email: str
    is_email_verified: bool
    is_active: bool
    date_joined: datetime

    class Config:
        from_attributes = True
