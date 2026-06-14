"""Serializers for plans and subscriptions."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.plans.models import Plan, UserSubscription

User = get_user_model()


class PlanSerializer(serializers.ModelSerializer):
    subscriber_count = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = [
            "id", "name", "description", "is_active", "is_default",
            "max_tenants", "rate_limit_per_minute", "requests_per_hour",
            "requests_per_day", "subscriber_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "subscriber_count", "created_at", "updated_at"]

    def get_subscriber_count(self, obj):
        return obj.subscriptions.filter(valid_to__isnull=True).count()


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.filter(is_active=True),
        source="plan",
        write_only=True,
    )
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = UserSubscription
        fields = [
            "id", "user_email", "plan", "plan_id",
            "valid_from", "valid_to", "created_at",
        ]
        read_only_fields = ["id", "user_email", "valid_from", "valid_to", "created_at"]


class MyPlanSerializer(serializers.Serializer):
    """Read-only view of a user's current plan and limits."""
    plan_name = serializers.CharField()
    max_tenants = serializers.IntegerField()
    rate_limit_per_minute = serializers.IntegerField()
    requests_per_hour = serializers.IntegerField()
    requests_per_day = serializers.IntegerField()
    tenants_used = serializers.IntegerField()
    valid_from = serializers.DateTimeField()
