"""ProcessRequest and ProcessResponse entities."""

from datetime import datetime

from pydantic import BaseModel, model_validator


class ProcessRequest(BaseModel):
    """Request payload for the process endpoint."""

    endpoint: str
    method: str = "POST"
    payload: dict | None = None

    @model_validator(mode="before")
    @classmethod
    def _accept_data_as_payload(cls, values: dict) -> dict:
        if isinstance(values, dict) and "data" in values and "payload" not in values:
            values["payload"] = values.pop("data")
        return values

    @property
    def data(self) -> dict | None:
        return self.payload


class ProcessResponse(BaseModel):
    """Response from the process endpoint."""

    success: bool
    message: str
    request_id: str
    tenant_id: str
    user_id: str
    processed_at: datetime
    rate_limit_remaining: int
    data: dict | None = None


class RateLimitExceededResponse(BaseModel):
    """Response when rate limit is exceeded."""

    error: str = "rate_limit_exceeded"
    message: str
    retry_after_seconds: int
    tenant_id: str
    user_id: str


class TokenInvalidResponse(BaseModel):
    """Response when token is invalid or expired."""

    error: str = "invalid_token"
    message: str
