"""Process endpoint router."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.api.dependencies import container
from app.application.process_request import ProcessRequestUseCase
from app.domain.process import (
    ProcessRequest,
    ProcessResponse,
    RateLimitExceededResponse,
    TokenInvalidResponse,
)
from app.infrastructure.postgres_adapter import PostgresAdapter
from app.infrastructure.redis_adapter import RedisAdapter


router = APIRouter(prefix="/api/v1", tags=["process"])


def extract_token(
    authorization: str | None,
    x_api_token: str | None = None,
) -> str:
    """Extract token from X-API-Token or Authorization: Bearer header."""
    if x_api_token:
        return x_api_token

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Authorization header is required",
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Use: Bearer <token>",
        )

    return parts[1]


def get_postgres_connection() -> str:
    """Get PostgreSQL connection string from environment."""
    import os

    host = os.getenv("POSTGRES_HOST", "postgres")
    db = os.getenv("POSTGRES_DB", "multitenant_db")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    return f"postgresql://{user}:{password}@{host}:5432/{db}"


def get_redis_url() -> str:
    """Get Redis URL from environment."""
    import os

    return os.getenv("REDIS_URL", "redis://redis:6379")


@router.post(
    "/process",
    response_model=ProcessResponse,
    responses={
        200: {
            "model": ProcessResponse,
            "description": "Request processed successfully",
        },
        401: {"model": TokenInvalidResponse, "description": "Invalid or expired token"},
        429: {
            "model": RateLimitExceededResponse,
            "description": "Rate limit exceeded",
        },
    },
)
async def process_request(
    request: ProcessRequest,
    authorization: Annotated[str | None, Header()] = None,
    x_api_token: Annotated[str | None, Header()] = None,
    postgres_connection: str = Depends(get_postgres_connection),
    redis_url: str = Depends(get_redis_url),
) -> ProcessResponse:
    """Process an API request with token validation and rate limiting."""
    token = extract_token(authorization, x_api_token)
    use_case = container.get_process_request(postgres_connection, redis_url)
    result = use_case.execute(token, request)

    if not result.success:
        if result.error == "invalid_token":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.message,
            )
        elif result.error == "rate_limit_exceeded":
            retry_after = result.retry_after_seconds or 60
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": result.message,
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

    if result.response is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error processing request",
        )

    return result.response


@router.get("/rate-limit-status")
async def get_rate_limit_status(
    authorization: Annotated[str | None, Header()] = None,
    x_api_token: Annotated[str | None, Header()] = None,
    postgres_connection: str = Depends(get_postgres_connection),
    redis_url: str = Depends(get_redis_url),
) -> dict:
    """Get current rate limit status without incrementing."""
    token = extract_token(authorization, x_api_token)

    from app.application.validate_token import ValidateTokenUseCase

    validate_use_case = container.get_validate_token(postgres_connection, redis_url)
    validation = validate_use_case.execute(token)

    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=validation.message,
        )

    plan = validation.plan
    redis = container.get_redis(redis_url)
    rate_limit_use_case = container.get_check_rate_limit(redis_url)

    minute_status = rate_limit_use_case.get_status(
        tenant_id=validation.tenant.id,
        user_id=validation.user.id,
        rate_limit=plan.rate_limit_per_minute if plan else 30,
    )
    quota = redis.get_quota_usage(validation.user.id)

    return {
        "tenant_id": validation.tenant.id,
        "tenant_name": validation.tenant.name,
        "plan": plan.plan_name if plan else "Free",
        "limits": {
            "rate_limit_per_minute": plan.rate_limit_per_minute if plan else 30,
            "requests_per_hour": plan.requests_per_hour if plan else 500,
            "requests_per_day": plan.requests_per_day if plan else 2_000,
        },
        "usage": {
            "minute": minute_status["current_usage"],
            "hour": quota["hour_usage"],
            "day": quota["day_usage"],
        },
        "remaining": {
            "minute": minute_status["remaining"],
            "hour": max(0, (plan.requests_per_hour if plan else 500) - quota["hour_usage"]),
            "day": max(0, (plan.requests_per_day if plan else 2_000) - quota["day_usage"]),
        },
    }
