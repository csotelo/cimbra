"""Serializers for user authentication."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ["email", "password"]

    def validate_email(self, value):
        """Validate email is unique."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def create(self, validated_data):
        """Create a new user."""
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            is_email_verified=False,
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile editing."""

    class Meta:
        model = User
        fields = ["email", "date_joined", "is_email_verified", "is_superuser"]
        read_only_fields = ["email", "date_joined", "is_email_verified", "is_superuser"]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""

    current_password = serializers.CharField(
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        min_length=8,
        style={"input_type": "password"},
    )
    confirm_password = serializers.CharField(
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        """Validate passwords match."""
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs

    def validate_current_password(self, value):
        """Validate current password is correct."""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for forgot password request."""

    email = serializers.EmailField()

    def validate_email(self, value):
        """Validate email exists."""
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value.lower()


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for password reset."""

    token = serializers.CharField()
    new_password = serializers.CharField(
        min_length=8,
        style={"input_type": "password"},
    )
    confirm_password = serializers.CharField(
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        """Validate token and passwords."""
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )

        token = attrs["token"]
        from django.utils import timezone

        user = User.objects.filter(
            password_reset_token=token,
            password_reset_token_expires__gt=timezone.now(),
        ).first()

        if not user:
            raise serializers.ValidationError({"token": "Invalid or expired token."})

        attrs["user"] = user
        return attrs


class VerifyEmailSerializer(serializers.Serializer):
    """Serializer for email verification."""

    token = serializers.CharField()

    def validate_token(self, value):
        """Validate verification token."""
        from django.utils import timezone

        user = User.objects.filter(
            email_verification_token=value,
            email_verification_token_expires__gt=timezone.now(),
        ).first()

        if not user:
            raise serializers.ValidationError("Invalid or expired verification token.")

        if user.is_email_verified:
            raise serializers.ValidationError("Email is already verified.")

        self._user = user
        return value

    def save(self):
        """Mark email as verified."""
        self._user.is_email_verified = True
        self._user.clear_verification_token()
        self._user.save()
