"""Tests for domain entities."""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.domain.api_token import APIToken
from app.domain.process import (
    ProcessRequest,
    ProcessResponse,
    RateLimitExceededResponse,
)
from app.domain.tenant import Tenant
from app.domain.user import User


class TestTenantEntity:
    """Tests for Tenant Pydantic entity."""

    def test_create_tenant(self):
        """Test creating a valid tenant."""
        now = datetime.now(timezone.utc)
        tenant = Tenant(
            id=1,
            name="Test Tenant",
            slug="test-tenant",
            is_active=True,
            max_users=10,
            rate_limit=60,
            created_at=now,
            updated_at=now,
        )
        assert tenant.id == 1
        assert tenant.name == "Test Tenant"
        assert tenant.slug == "test-tenant"
        assert tenant.is_active is True
        assert tenant.max_users == 10
        assert tenant.rate_limit == 60

    def test_tenant_default_rate_limit(self):
        """Test tenant default rate limit."""
        now = datetime.now(timezone.utc)
        tenant = Tenant(
            id=1,
            name="Test",
            slug="test",
            is_active=True,
            max_users=10,
            created_at=now,
            updated_at=now,
        )
        assert tenant.rate_limit == 60


class TestUserEntity:
    """Tests for User Pydantic entity."""

    def test_create_user(self):
        """Test creating a valid user."""
        now = datetime.now(timezone.utc)
        user = User(
            id=1,
            email="test@example.com",
            is_email_verified=True,
            is_active=True,
            date_joined=now,
        )
        assert user.id == 1
        assert user.email == "test@example.com"
        assert user.is_email_verified is True
        assert user.is_active is True

    def test_user_invalid_email(self):
        """Test user with invalid email raises error."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            User(
                id=1,
                email="invalid-email",
                is_email_verified=False,
                is_active=True,
                date_joined=now,
            )


class TestAPITokenEntity:
    """Tests for APIToken Pydantic entity."""

    def test_create_api_token(self):
        """Test creating a valid API token."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=365)
        token = APIToken(
            id=1,
            token="abc123",
            tenant_id=1,
            owner_id=1,
            is_active=True,
            expires_at=expires,
            created_at=now,
            updated_at=now,
        )
        assert token.token == "abc123"
        assert token.tenant_id == 1
        assert token.owner_id == 1
        assert token.is_active is True
        assert token.expires_at > now


class TestProcessRequestEntity:
    """Tests for ProcessRequest Pydantic entity."""

    def test_create_process_request(self):
        """Test creating a valid process request."""
        request = ProcessRequest(
            endpoint="/api/data",
            method="POST",
            data={"key": "value"},
        )
        assert request.endpoint == "/api/data"
        assert request.method == "POST"
        assert request.data == {"key": "value"}

    def test_process_request_defaults(self):
        """Test process request default values."""
        request = ProcessRequest(endpoint="/api/test")
        assert request.method == "POST"
        assert request.data is None


class TestProcessResponseEntity:
    """Tests for ProcessResponse Pydantic entity."""

    def test_create_process_response(self):
        """Test creating a valid process response."""
        now = datetime.now(timezone.utc)
        response = ProcessResponse(
            success=True,
            message="OK",
            request_id="req-123",
            tenant_id=1,
            user_id=1,
            processed_at=now,
            rate_limit_remaining=59,
            data={"result": "success"},
        )
        assert response.success is True
        assert response.request_id == "req-123"
        assert response.rate_limit_remaining == 59


class TestRateLimitExceededResponse:
    """Tests for RateLimitExceededResponse Pydantic entity."""

    def test_create_rate_limit_response(self):
        """Test creating a rate limit exceeded response."""
        response = RateLimitExceededResponse(
            message="Too many requests",
            retry_after_seconds=60,
            tenant_id=1,
            user_id=1,
        )
        assert response.error == "rate_limit_exceeded"
        assert response.retry_after_seconds == 60
