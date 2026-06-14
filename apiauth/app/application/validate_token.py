"""Token validation use case — JWT-based offline validation + Redis plan cache."""

import os
from dataclasses import dataclass
from datetime import datetime, timezone

import jwt

from app.domain.tenant import Tenant
from app.domain.user import User
from app.domain.user_tenant_role import UserTenantRole
from app.infrastructure.postgres_adapter import PostgresAdapter
from app.infrastructure.redis_adapter import RedisAdapter

_FREE_PLAN = {
    "plan_name": "Free",
    "rate_limit_per_minute": 30,
    "requests_per_hour": 500,
    "requests_per_day": 2_000,
}


@dataclass
class PlanLimits:
    plan_name: str
    rate_limit_per_minute: int
    requests_per_hour: int
    requests_per_day: int


@dataclass
class TokenValidationResult:
    valid: bool
    message: str
    user: User | None = None
    tenant: Tenant | None = None
    role: UserTenantRole | None = None
    plan: PlanLimits | None = None


class ValidateTokenUseCase:
    """Validates JWT API tokens.

    Flow:
      1. Decode JWT — verify signature and exp (no DB hit)
      2. Check token type == "api_key"
      3. Query DB for tenant is_active check
      4. Read plan limits from Redis cache (plan:{user_id})
         → on miss: query DB user_subscriptions → cache result 5 min
         → plan changes by Django immediately delete the cache key
    """

    def __init__(self, postgres_adapter: PostgresAdapter, redis_adapter: RedisAdapter):
        self._postgres = postgres_adapter
        self._redis = redis_adapter
        self._secret = os.getenv("FASTAPI_SECRET_KEY", "change-me-in-production")
        self._algorithm = os.getenv("FASTAPI_ALGORITHM", "HS256")

    def execute(self, token: str) -> TokenValidationResult:
        if not token:
            return TokenValidationResult(valid=False, message="Token is required")

        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.ExpiredSignatureError:
            return TokenValidationResult(valid=False, message="Token has expired")
        except jwt.InvalidTokenError as e:
            return TokenValidationResult(valid=False, message=f"Invalid token: {e}")

        if payload.get("type") != "api_key":
            return TokenValidationResult(valid=False, message="Invalid token type")

        tid = payload.get("tid")
        sub = payload.get("sub")
        role_value = payload.get("role")
        email = payload.get("email")
        iat = payload.get("iat")

        if not all([tid, sub, role_value, email]):
            return TokenValidationResult(valid=False, message="Incomplete token claims")

        tenant = self._postgres.get_tenant(tid)
        if tenant is None or not tenant.is_active:
            return TokenValidationResult(valid=False, message="Tenant not found or inactive")

        # Plan: Redis cache → DB fallback
        plan_data = self._redis.get_plan_cache(sub)
        if plan_data is None:
            plan_data = self._postgres.get_user_plan(sub)
            if plan_data:
                self._redis.set_plan_cache(sub, plan_data)
            else:
                plan_data = _FREE_PLAN

        plan = PlanLimits(
            plan_name=plan_data["plan_name"],
            rate_limit_per_minute=plan_data["rate_limit_per_minute"],
            requests_per_hour=plan_data["requests_per_hour"],
            requests_per_day=plan_data["requests_per_day"],
        )

        issued_at = datetime.fromtimestamp(iat, tz=timezone.utc) if iat else datetime.now(tz=timezone.utc)
        user = User(id=sub, email=email, is_email_verified=True, is_active=True, date_joined=issued_at)
        role = UserTenantRole(user_id=sub, tenant_id=tid, role=role_value)

        return TokenValidationResult(
            valid=True, message="Token is valid",
            user=user, tenant=tenant, role=role, plan=plan,
        )
