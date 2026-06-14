"""Exception handlers."""

import logging

from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.views import exception_handler

from core.middleware import get_current_tenant

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Custom exception handler with tenant-aware logging.

    Logs exceptions with tenant context for audit purposes.
    Adds tenant_id to response data for ValidationError and PermissionDenied.
    """
    response = exception_handler(exc, context)

    if response is not None:
        tenant = get_current_tenant()
        tenant_info = (
            {"tenant_id": str(tenant.id), "tenant_slug": tenant.slug}
            if tenant
            else {"tenant_id": None}
        )

        if isinstance(exc, (ValidationError, PermissionDenied)):
            response.data["tenant"] = tenant_info

        log_level = logging.WARNING if response.status_code < 500 else logging.ERROR
        logger.log(
            log_level,
            "Exception %s on %s %s (tenant: %s)",
            response.status_code,
            context.get("request").method if context.get("request") else "UNKNOWN",
            context.get("request").path if context.get("request") else "UNKNOWN",
            tenant.slug if tenant else "none",
        )

    return response
