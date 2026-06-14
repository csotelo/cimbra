"""Serializers for tenant management."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.tenants.models import Tenant, UserTenantRole

User = get_user_model()


class MemberUserSerializer(serializers.Serializer):
    """Nested user info for member list."""
    id = serializers.IntegerField()
    email = serializers.EmailField()


class TenantMemberSerializer(serializers.ModelSerializer):
    """Serializer for tenant member in member list."""

    user = MemberUserSerializer(read_only=True)
    role = serializers.ChoiceField(
        choices=UserTenantRole.Role.choices,
        required=True,
    )

    class Meta:
        model = UserTenantRole
        fields = ["id", "user", "role", "created_at"]


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for tenant CRUD operations.

    Used for creating, listing, and updating tenants.
    """

    member_count = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "slug",
            "is_active",
            "max_users",
            "rate_limit",
            "member_count",
            "is_owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "member_count",
            "is_owner",
            "created_at",
            "updated_at",
        ]

    def get_member_count(self, obj):
        """Get current member count."""
        return obj.member_roles.count()

    def get_is_owner(self, obj):
        """Check if current user is owner."""
        request = self.context.get("request")
        if not request or not hasattr(request, "user"):
            return False
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return UserTenantRole.objects.filter(
            user=user,
            tenant=obj,
            role=UserTenantRole.Role.OWNER,
        ).exists()

    def validate_name(self, value):
        """Validate and generate slug from name."""
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        return value.strip()

    def create(self, validated_data):
        user = self.context["request"].user
        if not user.can_create_tenant():
            raise serializers.ValidationError(
                {"detail": "Maximum number of owned tenants reached."}
            )
        tenant = Tenant.objects.create(**validated_data)
        tenant.add_owner(user)
        return tenant


class TenantUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating tenant fields (owner only)."""

    class Meta:
        model = Tenant
        fields = ["name", "is_active", "max_users", "rate_limit"]

    def validate_max_users(self, value):
        """Validate max_users is reasonable."""
        if value < 1:
            raise serializers.ValidationError("max_users must be at least 1.")
        return value

    def validate_rate_limit(self, value):
        """Validate rate_limit is reasonable."""
        if value < 1:
            raise serializers.ValidationError("rate_limit must be at least 1.")
        return value


class AddMemberSerializer(serializers.Serializer):
    """Serializer for adding a member to a tenant."""

    email = serializers.EmailField()

    def validate_email(self, value):
        """Validate email exists and user can be added."""
        email = value.lower()
        user = User.objects.filter(email__iexact=email).first()

        if not user:
            raise serializers.ValidationError("No user found with this email.")

        tenant = self.context.get("tenant")
        if not tenant:
            raise serializers.ValidationError("Tenant context required.")

        if not tenant.is_active:
            raise serializers.ValidationError("Tenant is not active.")

        existing = UserTenantRole.objects.filter(
            user=user,
            tenant=tenant,
        ).exists()

        if existing:
            raise serializers.ValidationError(
                "User is already a member of this tenant."
            )

        if not tenant.can_add_user():
            raise serializers.ValidationError(
                f"Tenant has reached maximum members ({tenant.max_users})."
            )

        return email

    def create(self, validated_data):
        """Add user to tenant as member."""
        email = validated_data["email"]
        user = User.objects.get(email__iexact=email)
        tenant = self.context["tenant"]
        role = self.context.get("role", UserTenantRole.Role.MEMBER)

        return UserTenantRole.objects.create(
            user=user,
            tenant=tenant,
            role=role,
        )


class ChangeMemberRoleSerializer(serializers.Serializer):
    """Serializer for changing a member's role."""

    role = serializers.ChoiceField(choices=UserTenantRole.Role.choices)

    def validate_role(self, value):
        """Validate role change is allowed."""
        user = self.context.get("user")
        tenant = self.context.get("tenant")
        current_user = self.context.get("request").user

        if not user or not tenant:
            raise serializers.ValidationError("Invalid context.")

        if user.id == current_user.id:
            raise serializers.ValidationError("Cannot change your own role.")

        target_membership = UserTenantRole.objects.get(user=user, tenant=tenant)

        if target_membership.role == UserTenantRole.Role.OWNER:
            raise serializers.ValidationError("Cannot change owner's role.")

        return value
