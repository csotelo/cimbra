"""Models for API token management."""

import uuid
from datetime import timedelta

import jwt
from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import BaseModel


class APIToken(BaseModel):
    """API token for tenant owner authentication.

    An owner can have only 1 active token per tenant.
    The token is shown in plain text only once when created.
    Token format: signed JWT with claims {sub, email, tid, tname, role, jti, iat, exp, type}.
    """

    token = models.CharField(
        max_length=512,
        unique=True,
        db_index=True,
    )

    owner = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        related_name="api_tokens",
    )

    expires_at = models.DateTimeField()

    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "api_tokens"
        verbose_name = "API Token"
        verbose_name_plural = "API Tokens"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Token for {self.tenant.name} by {self.owner.email}"

    @classmethod
    def get_expiry_days(cls):
        """Get token expiry days from settings."""
        return getattr(settings, "API_TOKEN_EXPIRY_DAYS", 365)

    @classmethod
    def generate_jwt(cls, tenant, owner, role_value, expires_at):
        """Generate a signed JWT API token with identity claims only.

        Plan limits are NOT embedded in the JWT — apiauth reads them from
        Redis (or DB on cache miss) on every request. This guarantees that
        plan changes (especially downgrades) take effect immediately without
        requiring token regeneration.
        """
        payload = {
            "sub": str(owner.id),
            "email": owner.email,
            "tid": str(tenant.id),
            "tname": tenant.name,
            "role": role_value,
            "jti": str(uuid.uuid4()),
            "iat": int(timezone.now().timestamp()),
            "exp": int(expires_at.timestamp()),
            "type": "api_key",
        }
        return jwt.encode(payload, settings.JWT_API_TOKEN_SECRET, algorithm="HS256")

    @classmethod
    def create_for_tenant(cls, tenant, owner):
        """Create a new JWT token for tenant and owner.

        Revokes any existing active token for this owner-tenant pair.
        """
        from apps.tenants.models import UserTenantRole

        cls.objects.filter(
            tenant=tenant,
            owner=owner,
            is_active=True,
        ).update(is_active=False)

        expiry_days = cls.get_expiry_days()
        expires_at = timezone.now() + timedelta(days=expiry_days)

        membership = UserTenantRole.objects.filter(user=owner, tenant=tenant).first()
        role_value = membership.role if membership else UserTenantRole.Role.OWNER

        token_value = cls.generate_jwt(tenant, owner, role_value, expires_at)

        return cls.objects.create(
            token=token_value,
            tenant=tenant,
            owner=owner,
            expires_at=expires_at,
            is_active=True,
        )

    @property
    def is_expired(self):
        """Check if token has passed its expiry date."""
        from django.utils import timezone

        return self.expires_at < timezone.now()

    @property
    def is_valid(self):
        """Check if token is active and not expired."""
        return self.is_active and not self.is_expired

    def revoke(self):
        """Revoke this token."""
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])
