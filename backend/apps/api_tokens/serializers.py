"""Serializers for API token management."""

from rest_framework import serializers

from apps.api_tokens.models import APIToken


class APITokenCreateSerializer(serializers.Serializer):
    """Serializer for creating a new API token.

    The token value is only returned once upon creation.
    """

    def create(self, validated_data):
        """Create and return a new token."""
        tenant = self.context.get("tenant")
        owner = self.context.get("owner")
        token_obj = APIToken.create_for_tenant(tenant, owner)
        return token_obj


class APITokenResponseSerializer(serializers.ModelSerializer):
    """Serializer for token creation response.

    Returns the token value only once.
    """

    token = serializers.CharField(read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = APIToken
        fields = [
            "id",
            "token",
            "tenant",
            "is_valid",
            "is_expired",
            "expires_at",
            "created_at",
        ]


class APITokenStatusSerializer(serializers.ModelSerializer):
    """Serializer for viewing token status.

    Never returns the actual token value.
    """

    is_valid = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    owner_email = serializers.CharField(source="owner.email", read_only=True)

    class Meta:
        model = APIToken
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "owner_email",
            "is_valid",
            "is_expired",
            "expires_at",
            "last_used_at",
            "is_active",
            "created_at",
        ]
        read_only_fields = fields
