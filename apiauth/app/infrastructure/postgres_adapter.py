"""PostgreSQL adapter using SQLAlchemy Core (read-only).

This adapter provides read-only access to Django's PostgreSQL database.
FastAPI does NOT write to the database - only reads.
"""

import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    UUID,
    create_engine,
    select,
)
from sqlalchemy.engine import Engine

from app.domain.api_token import APIToken
from app.domain.tenant import Tenant
from app.domain.user import User
from app.domain.user_tenant_role import UserTenantRole


metadata = MetaData()

custom_users = Table(
    "custom_users",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("password", String(128)),
    Column("email", String(255), unique=True),
    Column("is_email_verified", Boolean, default=False),
    Column("is_active", Boolean, default=True),
    Column("is_staff", Boolean, default=False),
    Column("is_superuser", Boolean, default=False),
    Column("date_joined", DateTime),
    Column("last_login", DateTime, nullable=True),
)

tenants = Table(
    "tenants",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("name", String(255)),
    Column("slug", String(100), unique=True),
    Column("is_active", Boolean, default=True),
    Column("max_users", Integer, default=10),
    Column("rate_limit", Integer, default=100),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
)

api_tokens = Table(
    "api_tokens",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("token", String(512), unique=True),
    Column("tenant_id", UUID, ForeignKey("tenants.id")),
    Column("owner_id", BigInteger, ForeignKey("custom_users.id")),
    Column("is_active", Boolean, default=True),
    Column("expires_at", DateTime, nullable=True),
    Column("last_used_at", DateTime, nullable=True),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
)

user_tenant_roles = Table(
    "user_tenant_roles",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("user_id", BigInteger, ForeignKey("custom_users.id")),
    Column("tenant_id", UUID, ForeignKey("tenants.id")),
    Column("role", String(10)),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
)

plans = Table(
    "plans",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("name", String(100)),
    Column("rate_limit_per_minute", Integer),
    Column("requests_per_hour", Integer),
    Column("requests_per_day", Integer),
    Column("is_active", Boolean),
)

user_subscriptions = Table(
    "user_subscriptions",
    metadata,
    Column("id", UUID, primary_key=True),
    Column("user_id", BigInteger, ForeignKey("custom_users.id")),
    Column("plan_id", UUID, ForeignKey("plans.id")),
    Column("valid_from", DateTime),
    Column("valid_to", DateTime, nullable=True),
)


class PostgresAdapter:
    """Read-only PostgreSQL adapter using SQLAlchemy Core.

    FastAPI uses this adapter to read data from Django's tables.
    NO writes are performed - only SELECT queries.
    """

    def __init__(self, connection_string: str):
        self._engine: Engine = create_engine(
            connection_string,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )

    @contextmanager
    def _connection(self):
        """Context manager for database connections."""
        conn = self._engine.connect()
        try:
            yield conn
        finally:
            conn.close()

    def get_api_token(self, token: str) -> APIToken | None:
        """Get API token by token string (read-only).

        Args:
            token: The API token string

        Returns:
            APIToken entity or None if not found
        """
        query = select(api_tokens).where(api_tokens.c.token == token)
        with self._connection() as conn:
            result = conn.execute(query).fetchone()
            if result is None:
                return None
            return APIToken(
                id=str(result.id),
                token=result.token,
                tenant_id=str(result.tenant_id),
                owner_id=str(result.owner_id),
                is_active=result.is_active,
                expires_at=result.expires_at,
                last_used_at=result.last_used_at,
                created_at=result.created_at,
                updated_at=result.updated_at,
            )

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        """Get tenant by UUID string (read-only)."""
        query = select(tenants).where(tenants.c.id == uuid.UUID(tenant_id))
        with self._connection() as conn:
            result = conn.execute(query).fetchone()
            if result is None:
                return None
            return Tenant(
                id=str(result.id),
                name=result.name,
                slug=result.slug,
                is_active=result.is_active,
                max_users=result.max_users,
                rate_limit=result.rate_limit,
                created_at=result.created_at,
                updated_at=result.updated_at,
            )

    def get_user(self, user_id) -> User | None:
        """Get user by ID (read-only).

        Args:
            user_id: The user ID

        Returns:
            User entity or None if not found
        """
        query = select(custom_users).where(custom_users.c.id == user_id)
        with self._connection() as conn:
            result = conn.execute(query).fetchone()
            if result is None:
                return None
            return User(
                id=str(result.id),
                email=result.email,
                is_email_verified=result.is_email_verified,
                is_active=result.is_active,
                date_joined=result.date_joined,
            )

    def get_user_tenant_role(self, user_id, tenant_id) -> UserTenantRole | None:
        """Get user's role in a tenant (read-only).

        Args:
            user_id: The user ID
            tenant_id: The tenant ID

        Returns:
            UserTenantRole entity or None if not found
        """
        query = select(user_tenant_roles).where(
            user_tenant_roles.c.user_id == user_id,
            user_tenant_roles.c.tenant_id == tenant_id,
        )
        with self._connection() as conn:
            result = conn.execute(query).fetchone()
            if result is None:
                return None
            return UserTenantRole(
                user_id=str(result.user_id),
                tenant_id=str(result.tenant_id),
                role=result.role,
            )

    def validate_token(self, token: str) -> dict[str, Any] | None:
        """Validate token and return associated data.

        Args:
            token: The API token string

        Returns:
            Dict with token, user, tenant, and role data, or None if invalid
        """
        api_token = self.get_api_token(token)
        if api_token is None:
            return None

        if not api_token.is_active:
            return None

        if api_token.expires_at and api_token.expires_at < datetime.now(timezone.utc):
            return None

        tenant = self.get_tenant(api_token.tenant_id)
        if tenant is None or not tenant.is_active:
            return None

        user = self.get_user(api_token.owner_id)
        if user is None or not user.is_active:
            return None

        role = self.get_user_tenant_role(api_token.owner_id, api_token.tenant_id)
        if role is None:
            return None

        return {
            "token": api_token,
            "user": user,
            "tenant": tenant,
            "role": role,
        }

    def get_user_plan(self, user_id: str) -> dict | None:
        """Get user's active plan limits from DB (called on cache miss)."""
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            return None

        query = (
            select(
                plans.c.name,
                plans.c.rate_limit_per_minute,
                plans.c.requests_per_hour,
                plans.c.requests_per_day,
            )
            .select_from(
                user_subscriptions.join(plans, user_subscriptions.c.plan_id == plans.c.id)
            )
            .where(
                user_subscriptions.c.user_id == uid,
                user_subscriptions.c.valid_to.is_(None),
            )
        )
        with self._connection() as conn:
            result = conn.execute(query).fetchone()
            if result is None:
                return None
            return {
                "plan_name": result.name,
                "rate_limit_per_minute": result.rate_limit_per_minute,
                "requests_per_hour": result.requests_per_hour,
                "requests_per_day": result.requests_per_day,
            }

    def close(self):
        """Close the database engine."""
        self._engine.dispose()
