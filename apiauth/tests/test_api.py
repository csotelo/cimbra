"""Tests for API endpoints."""

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.process_request import ProcessResult
from app.domain.api_token import APIToken
from app.domain.process import ProcessResponse
from app.domain.tenant import Tenant
from app.domain.user import User


@pytest.fixture
def mock_container():
    """Create mock container."""
    with patch("app.api.routes.process.container") as mock:
        yield mock


@pytest.fixture
def test_client():
    """Create FastAPI test client."""
    from app.main import app

    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health endpoint."""

    def test_health_check(self, test_client):
        """Test health check returns healthy status."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestProcessEndpoint:
    """Tests for process endpoint."""

    def test_process_missing_auth_header(self, test_client, mock_container):
        """Test process without Authorization header."""
        response = test_client.post(
            "/api/v1/process",
            json={"endpoint": "/api/test"},
        )
        assert response.status_code == 422

    def test_process_invalid_auth_format(self, test_client, mock_container):
        """Test process with invalid Authorization format."""
        response = test_client.post(
            "/api/v1/process",
            json={"endpoint": "/api/test"},
            headers={"Authorization": "InvalidFormat"},
        )
        assert response.status_code == 401
        assert "Invalid Authorization header format" in response.json()["detail"]

    def test_process_invalid_token(self, test_client, mock_container):
        """Test process with invalid token."""
        mock_use_case = MagicMock()
        mock_use_case.execute.return_value = ProcessResult(
            success=False,
            message="Invalid or expired token",
            error="invalid_token",
            status_code=401,
        )
        mock_container.get_process_request.return_value = mock_use_case

        response = test_client.post(
            "/api/v1/process",
            json={"endpoint": "/api/test"},
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_process_rate_limit_exceeded(self, test_client, mock_container):
        """Test process when rate limit exceeded."""
        mock_use_case = MagicMock()
        mock_response = MagicMock()
        mock_response.rate_limit_remaining = 30
        mock_use_case.execute.return_value = ProcessResult(
            success=False,
            message="Rate limit exceeded",
            error="rate_limit_exceeded",
            status_code=429,
            response=mock_response,
        )
        mock_container.get_process_request.return_value = mock_use_case

        response = test_client.post(
            "/api/v1/process",
            json={"endpoint": "/api/test"},
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 429

    def test_process_success(self, test_client, mock_container):
        """Test successful process."""
        now = datetime.now(timezone.utc)
        mock_use_case = MagicMock()
        mock_use_case.execute.return_value = ProcessResult(
            success=True,
            message="OK",
            response=ProcessResponse(
                success=True,
                message="OK",
                request_id="req-123",
                tenant_id=1,
                user_id=1,
                processed_at=now,
                rate_limit_remaining=59,
                data={"result": "success"},
            ),
        )
        mock_container.get_process_request.return_value = mock_use_case

        response = test_client.post(
            "/api/v1/process",
            json={"endpoint": "/api/test", "method": "POST"},
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["request_id"] == "req-123"


class TestRateLimitStatusEndpoint:
    """Tests for rate limit status endpoint."""

    def test_rate_limit_status_missing_auth(self, test_client, mock_container):
        """Test rate limit status without auth."""
        response = test_client.get("/api/v1/rate-limit-status")
        assert response.status_code == 422

    def test_rate_limit_status_invalid_token(self, test_client, mock_container):
        """Test rate limit status with invalid token."""
        mock_validate = MagicMock()
        mock_validate.execute.return_value = MagicMock(
            valid=False, message="Invalid", tenant=None, user=None
        )
        mock_container.get_validate_token.return_value = mock_validate

        response = test_client.get(
            "/api/v1/rate-limit-status",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_rate_limit_status_success(self, test_client, mock_container):
        """Test rate limit status with valid token."""
        now = datetime.now(timezone.utc)

        mock_validate = MagicMock()
        mock_validate.execute.return_value = MagicMock(
            valid=True,
            user=MagicMock(id=1),
            tenant=MagicMock(id=1, name="Test", rate_limit=60),
        )
        mock_container.get_validate_token.return_value = mock_validate

        mock_rate_limit = MagicMock()
        mock_rate_limit.get_status.return_value = {
            "limit": 60,
            "remaining": 59,
            "window_seconds": 60,
            "current_usage": 1,
        }
        mock_container.get_check_rate_limit.return_value = mock_rate_limit

        response = test_client.get(
            "/api/v1/rate-limit-status",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == 1
        assert data["remaining"] == 59
