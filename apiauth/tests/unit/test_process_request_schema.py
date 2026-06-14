"""Unit tests for ProcessRequest schema — CA02 payload field contract.

These tests verify that the domain model exposes 'payload' as the canonical
field name, matching the acceptance.feature contract. They will FAIL until
ProcessRequest is updated to use 'payload' instead of (or as alias for) 'data'.
"""

import pytest

from app.domain.process import ProcessRequest


def test_process_request_accepts_payload_field():
    """ProcessRequest must accept 'payload' as request body field (CA02 contract)."""
    request = ProcessRequest(endpoint="/test", payload={"key": "value"})
    assert request.payload == {"key": "value"}


def test_process_request_payload_is_not_silently_dropped():
    """ProcessRequest must not silently discard the 'payload' field."""
    request = ProcessRequest(endpoint="/api/data", payload={"item_id": 42})
    assert hasattr(request, "payload")
    assert request.payload is not None
