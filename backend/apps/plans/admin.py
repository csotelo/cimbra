"""Admin registration for plans."""

from django.contrib import admin

from apps.plans.models import Plan, UserSubscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ["name", "max_tenants", "rate_limit_per_minute", "requests_per_hour", "requests_per_day", "is_default", "is_active"]
    list_filter = ["is_active", "is_default"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = [
        (None, {"fields": ["id", "name", "description", "is_active", "is_default"]}),
        ("Límites", {"fields": ["max_tenants", "rate_limit_per_minute", "requests_per_hour", "requests_per_day"]}),
        ("Timestamps", {"fields": ["created_at", "updated_at"]}),
    ]


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "valid_from", "valid_to", "changed_by"]
    list_filter = ["plan"]
    search_fields = ["user__email"]
    readonly_fields = ["id", "created_at"]
    raw_id_fields = ["user", "changed_by"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "plan", "changed_by")
