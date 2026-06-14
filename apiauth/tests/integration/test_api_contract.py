"""Integration tests for the API contract defined in acceptance.feature [US06].

CA02: POST /api/v1/process with X-API-Token header must return 401 for invalid tokens.
CA03: GET /api/v1/rate-limit-status with X-API-Token must validate the token.

All tests in this file will FAIL until the route layer is updated to:
  - Accept 'X-API-Token' header (in addition to or instead of 'Authorization: Bearer')
  - Forward the 'payload' body field to the use case without dropping it
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.application.process_request import ProcessResult
from app.domain.process import ProcessResponse


@pytest.fixture
def mock_container():
    """Patch the DI container so tests do not need real Postgres/Redis."""
    with patch("app.api.routes.process.container") as mock:
        yield mock


@pytest.fixture
def test_client():
    """Create a FastAPI TestClient against the app."""
    from app.main import app

    return TestClient(app)


# ---------------------------------------------------------------------------
# CA02 — POST /api/v1/process with X-API-Token header
# ---------------------------------------------------------------------------


class TestCA02XApiTokenHeaderSupport:
    """The process endpoint must recognise the X-API-Token header (CA02)."""

    def test_process_with_x_api_token_invalid_returns_401(
        self, test_client, mock_container
    ):
        """POST with X-API-Token: invalid-token-xyz must return 401, not 422.

        Currently returns 422 because the route requires the 'Authorization' header.
        The developer must add X-API-Token header support.
        """
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
            json={"endpoint": "/test", "payload": {}},
            headers={"X-API-Token": "invalid-token-xyz"},
        )
        assert response.status_code == 401

    def test_process_with_x_api_token_valid_returns_200(
        self, test_client, mock_container
    ):
        """POST with a valid X-API-Token must return 200 with process response."""
        now = datetime.now(timezone.utc)
        mock_use_case = MagicMock()
        mock_use_case.execute.return_value = ProcessResult(
            success=True,
            message="OK",
            response=ProcessResponse(
                success=True,
                message="OK",
                request_id="req-001",
                tenant_id=1,
                user_id=1,
                processed_at=now,
                rate_limit_remaining=59,
            ),
        )
        mock_container.get_process_request.return_value = mock_use_case

        response = test_client.post(
            "/api/v1/process",
            json={"endpoint": "/test", "payload": {"data": "value"}},
            headers={"X-API-Token": "valid-token-abc"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["request_id"] == "req-001"

    def test_process_body_payload_field_is_forwarded_to_use_case(
        self, test_client, mock_container
    ):
        """The 'payload' field in the request body must reach the use case, not be dropped.

        Currently ProcessRequest has 'data' instead of 'payload', so the field
        is silently discarded by Pydantic. The developer must rename or alias the field.
        """
        now = datetime.now(timezone.utc)
        captured = []

        def capture_execute(token, request):
            captured.append(request)
            return ProcessResult(
                success=True,
                message="OK",
                response=ProcessResponse(
                    success=True,
                    message="OK",
                    request_id="req-001",
                    tenant_id=1,
                    user_id=1,
                    processed_at=now,
                    rate_limit_remaining=58,
                ),
            )

        mock_use_case = MagicMock()
        mock_use_case.execute.side_effect = capture_execute
        mock_container.get_process_request.return_value = mock_use_case

        test_client.post(
            "/api/v1/process",
            json={"endpoint": "/test", "payload": {"item_id": 99}},
            headers={"X-API-Token": "valid-token-abc"},
        )

        assert len(captured) == 1, "use case was not called"
        assert captured[0].payload == {"item_id": 99}


# ---------------------------------------------------------------------------
# CA03 — GET /api/v1/rate-limit-status with X-API-Token header
# ---------------------------------------------------------------------------


class TestCA03RateLimitStatusXApiTokenHeader:
    """The rate-limit-status endpoint must recognise X-API-Token (CA03 extension)."""

    def test_rate_limit_status_with_x_api_token_invalid_returns_401(
        self, test_client, mock_container
    ):
        """GET rate-limit-status with invalid X-API-Token must return 401.

        Currently returns 422 because the route requires 'Authorization' header.
        """
        mock_validate = MagicMock()
        mock_validate.execute.return_value = MagicMock(
            valid=False,
            message="Invalid or expired token",
            tenant=None,
            user=None,
        )
        mock_container.get_validate_token.return_value = mock_validate

        response = test_client.get(
            "/api/v1/rate-limit-status",
            headers={"X-API-Token": "invalid-token-xyz"},
        )
        assert response.status_code == 401
