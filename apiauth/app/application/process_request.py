"""Process request use case."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from app.application.check_rate_limit import CheckRateLimitUseCase
from app.application.validate_token import ValidateTokenUseCase
from app.domain.process import ProcessRequest, ProcessResponse
from app.domain.tenant import Tenant
from app.domain.user import User
from app.domain.user_tenant_role import UserTenantRole


@dataclass
class ProcessResult:
    """Result of process request use case."""

    success: bool
    message: str
    response: ProcessResponse | None = None
    error: str | None = None
    status_code: int = 200
    retry_after_seconds: int | None = None


class ProcessRequestUseCase:
    """Use case for processing API requests.

    This use case orchestrates:
    1. Token validation
    2. Rate limit checking
    3. Request processing

    Returns a ProcessResponse on success or error information on failure.
    """

    def __init__(
        self,
        validate_token: ValidateTokenUseCase,
        check_rate_limit: CheckRateLimitUseCase,
    ):
        self._validate_token = validate_token
        self._check_rate_limit = check_rate_limit

    def execute(
        self,
        token: str,
        request: ProcessRequest,
    ) -> ProcessResult:
        """Execute request processing.

        Args:
            token: The API token from Authorization header
            request: The process request payload

        Returns:
            ProcessResult with response or error information
        """
        validation = self._validate_token.execute(token)

        if not validation.valid:
            return ProcessResult(
                success=False,
                message=validation.message,
                error="invalid_token",
                status_code=401,
            )

        plan = validation.plan
        rate_limit = self._check_rate_limit.execute(
            user_id=validation.user.id,
            rate_limit_per_minute=plan.rate_limit_per_minute if plan else 30,
            requests_per_hour=plan.requests_per_hour if plan else 500,
            requests_per_day=plan.requests_per_day if plan else 2_000,
            endpoint=request.endpoint,
            tenant_id=validation.tenant.id,
        )

        if not rate_limit.allowed:
            return ProcessResult(
                success=False,
                message=(
                    f"Rate limit exceeded. "
                    f"Retry after {rate_limit.retry_after_seconds} seconds."
                ),
                error="rate_limit_exceeded",
                status_code=429,
                retry_after_seconds=rate_limit.retry_after_seconds,
            )

        response = ProcessResponse(
            success=True,
            message="Request processed successfully",
            request_id=str(uuid.uuid4()),
            tenant_id=validation.tenant.id,
            user_id=validation.user.id,
            processed_at=datetime.utcnow(),
            rate_limit_remaining=rate_limit.remaining,
            data={
                "endpoint": request.endpoint,
                "method": request.method,
                "tenant": validation.tenant.name,
                "user": validation.user.email,
                "role": validation.role.role,
            },
        )

        return ProcessResult(
            success=True,
            message="Request processed successfully",
            response=response,
        )
