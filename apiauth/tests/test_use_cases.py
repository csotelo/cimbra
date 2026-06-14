"""Tests for use cases."""

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.application.check_rate_limit import CheckRateLimitUseCase
from app.application.process_request import ProcessRequestUseCase
from app.application.validate_token import ValidateTokenUseCase
from app.domain.api_token import APIToken
from app.domain.process import ProcessRequest
from app.domain.tenant import Tenant
from app.domain.user import User
from app.domain.user_tenant_role import UserTenantRole


class TestValidateTokenUseCase:
    """Tests for ValidateTokenUseCase."""

    @pytest.fixture
    def mock_postgres(self):
        """Create mock PostgreSQL adapter."""
        return MagicMock()

    @pytest.fixture
    def use_case(self, mock_postgres):
        """Create ValidateTokenUseCase with mock."""
        return ValidateTokenUseCase(mock_postgres)

    def test_validate_empty_token(self, use_case):
        """Test validation with empty token."""
        result = use_case.execute("")
        assert result.valid is False
        assert result.message == "Token is required"

    def test_validate_none_token(self, use_case):
        """Test validation with None token."""
        result = use_case.execute(None)
        assert result.valid is False
        assert result.message == "Token is required"

    def test_validate_invalid_token(self, use_case, mock_postgres):
        """Test validation with invalid token."""
        mock_postgres.validate_token.return_value = None
        result = use_case.execute("invalid-token")
        assert result.valid is False
        assert result.message == "Invalid or expired token"

    def test_validate_valid_token(self, use_case, mock_postgres):
        """Test validation with valid token."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=365)

        mock_postgres.validate_token.return_value = {
            "token": APIToken(
                id=1,
                token="valid-token",
                tenant_id=1,
                owner_id=1,
                is_active=True,
                expires_at=expires,
                created_at=now,
                updated_at=now,
            ),
            "user": User(
                id=1,
                email="test@example.com",
                is_email_verified=True,
                is_active=True,
                date_joined=now,
            ),
            "tenant": Tenant(
                id=1,
                name="Test",
                slug="test",
                is_active=True,
                max_users=10,
                rate_limit=60,
                created_at=now,
                updated_at=now,
            ),
            "role": UserTenantRole(user_id=1, tenant_id=1, role="owner"),
        }

        result = use_case.execute("valid-token")
        assert result.valid is True
        assert result.user.email == "test@example.com"
        assert result.tenant.name == "Test"
        assert result.role.role == "owner"


class TestCheckRateLimitUseCase:
    """Tests for CheckRateLimitUseCase."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis adapter."""
        return MagicMock()

    @pytest.fixture
    def use_case(self, mock_redis):
        """Create CheckRateLimitUseCase with mock."""
        return CheckRateLimitUseCase(mock_redis, window_seconds=60)

    def test_check_rate_limit_allowed(self, use_case, mock_redis):
        """Test rate limit check when allowed."""
        mock_redis.check_rate_limit.return_value = (True, 59, 0)

        result = use_case.execute(
            tenant_id=1,
            user_id=1,
            rate_limit=60,
            endpoint="/api/test",
        )

        assert result.allowed is True
        assert result.remaining == 59
        assert result.limit == 60

    def test_check_rate_limit_exceeded(self, use_case, mock_redis):
        """Test rate limit check when exceeded."""
        mock_redis.check_rate_limit.return_value = (False, 0, 30)
        mock_redis.publish_rate_limit_event = MagicMock()

        result = use_case.execute(
            tenant_id=1,
            user_id=1,
            rate_limit=60,
            endpoint="/api/test",
        )

        assert result.allowed is False
        assert result.retry_after_seconds == 30
        mock_redis.publish_rate_limit_event.assert_called_once_with(
            tenant_id=1,
            user_id=1,
            endpoint="/api/test",
            retry_after=30,
        )


class TestProcessRequestUseCase:
    """Tests for ProcessRequestUseCase."""

    @pytest.fixture
    def mock_validate_token(self):
        """Create mock ValidateTokenUseCase."""
        return MagicMock(spec=ValidateTokenUseCase)

    @pytest.fixture
    def mock_check_rate_limit(self):
        """Create mock CheckRateLimitUseCase."""
        return MagicMock(spec=CheckRateLimitUseCase)

    @pytest.fixture
    def use_case(self, mock_validate_token, mock_check_rate_limit):
        """Create ProcessRequestUseCase with mocks."""
        return ProcessRequestUseCase(mock_validate_token, mock_check_rate_limit)

    def test_process_invalid_token(self, use_case, mock_validate_token):
        """Test process with invalid token."""
        mock_validate_token.execute.return_value = MagicMock(
            valid=False,
            message="Invalid token",
        )

        request = ProcessRequest(endpoint="/api/test")
        result = use_case.execute("invalid-token", request)

        assert result.success is False
        assert result.error == "invalid_token"
        assert result.status_code == 401

    def test_process_rate_limit_exceeded(
        self, use_case, mock_validate_token, mock_check_rate_limit
    ):
        """Test process when rate limit exceeded."""
        now = datetime.now(timezone.utc)

        mock_validate_token.execute.return_value = MagicMock(
            valid=True,
            message="OK",
            user=MagicMock(id=1, email="test@example.com"),
            tenant=MagicMock(id=1, name="Test", rate_limit=60),
            role=MagicMock(role="owner"),
        )

        mock_check_rate_limit.execute.return_value = MagicMock(
            allowed=False,
            remaining=0,
            retry_after_seconds=30,
        )

        request = ProcessRequest(endpoint="/api/test")
        result = use_case.execute("valid-token", request)

        assert result.success is False
        assert result.error == "rate_limit_exceeded"
        assert result.status_code == 429

    def test_process_success(
        self, use_case, mock_validate_token, mock_check_rate_limit
    ):
        """Test successful process."""
        now = datetime.now(timezone.utc)

        mock_validate_token.execute.return_value = MagicMock(
            valid=True,
            message="OK",
            user=MagicMock(id=1, email="test@example.com"),
            tenant=MagicMock(id=1, name="Test", rate_limit=60),
            role=MagicMock(role="owner"),
        )

        mock_check_rate_limit.execute.return_value = MagicMock(
            allowed=True,
            remaining=59,
            retry_after_seconds=0,
        )

        request = ProcessRequest(endpoint="/api/test")
        result = use_case.execute("valid-token", request)

        assert result.success is True
        assert result.response is not None
        assert result.response.success is True
        assert result.status_code == 200
