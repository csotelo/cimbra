"""Views for plan self-service."""

from datetime import datetime, timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.plans.models import UserSubscription
from apps.tenants.models import Tenant, UserTenantRole


class MyUsageView(APIView):
    """Current rate limit usage for the authenticated user — reads Redis directly.

    GET /api/plans/usage/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        import os
        import redis as redis_lib

        sub = UserSubscription.get_active(request.user)
        if not sub:
            return Response({"detail": "Sin plan activo."}, status=404)

        user_id = str(request.user.id)
        now = datetime.now(timezone.utc)
        hour_slot = now.strftime("%Y%m%d%H")
        day_slot = now.strftime("%Y%m%d")

        try:
            r = redis_lib.from_url(os.getenv("REDIS_URL", "redis://redis:6379"), decode_responses=True)
            minute_key = f"rl:min:{user_id}"
            r.zremrangebyscore(minute_key, 0, now.timestamp() - 60)
            minute_usage = r.zcard(minute_key)
            hour_usage = int(r.get(f"rl:hour:{user_id}:{hour_slot}") or 0)
            day_usage = int(r.get(f"rl:day:{user_id}:{day_slot}") or 0)
            r.close()
        except Exception:
            minute_usage = hour_usage = day_usage = 0

        p = sub.plan
        return Response({
            "plan": p.name,
            "limits": {
                "rate_limit_per_minute": p.rate_limit_per_minute,
                "requests_per_hour": p.requests_per_hour,
                "requests_per_day": p.requests_per_day,
            },
            "usage": {
                "minute": minute_usage,
                "hour": hour_usage,
                "day": day_usage,
            },
            "remaining": {
                "minute": max(0, p.rate_limit_per_minute - minute_usage),
                "hour": max(0, p.requests_per_hour - hour_usage),
                "day": max(0, p.requests_per_day - day_usage),
            },
        })


class MyPlanView(APIView):
    """Plan activo del usuario autenticado.

    GET /api/plans/me/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub = UserSubscription.get_active(request.user)
        if not sub:
            return Response({"detail": "Sin plan activo."}, status=404)

        tenants_owned = Tenant.objects.filter(
            member_roles__user=request.user,
            member_roles__role=UserTenantRole.Role.OWNER,
            is_active=True,
        ).count()

        return Response({
            "plan_name": sub.plan.name,
            "max_tenants": sub.plan.max_tenants,
            "rate_limit_per_minute": sub.plan.rate_limit_per_minute,
            "requests_per_hour": sub.plan.requests_per_hour,
            "requests_per_day": sub.plan.requests_per_day,
            "tenants_used": tenants_owned,
            "valid_from": sub.valid_from,
        })
