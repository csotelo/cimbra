"""Dashboard API views."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboard.models import UserDashboard, Widget


class DashboardWidgetsView(APIView):
    """Returns the user's dashboard widget layout.

    GET  /api/dashboard/  — list widgets with user preferences
    POST /api/dashboard/  — update visibility/position for a widget
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        prefs = {
            p.widget_id: p
            for p in UserDashboard.objects.filter(user=request.user).select_related("widget__module")
        }

        qs = Widget.objects.filter(module__is_enabled=True)
        if not request.user.is_superuser:
            qs = qs.filter(is_staff_only=False)
        widgets = qs.select_related("module").order_by("module__slug", "name")

        result = []
        for widget in widgets:
            pref = prefs.get(widget.id)
            result.append({
                "id": str(widget.id),
                "module": widget.module.slug,
                "name": widget.name,
                "label": widget.label,
                "description": widget.description,
                "vue_component": widget.vue_component,
                "is_visible": pref.is_visible if pref else widget.default_visible,
                "position": pref.position if pref else 999,
            })

        result.sort(key=lambda w: w["position"])
        return Response(result)

    def post(self, request):
        """Update widget preference. Body: {widget_id, is_visible, position}"""
        widget_id = request.data.get("widget_id")
        try:
            widget = Widget.objects.get(id=widget_id, module__is_enabled=True)
        except Widget.DoesNotExist:
            return Response({"detail": "Widget no encontrado."}, status=404)

        pref, _ = UserDashboard.objects.get_or_create(
            user=request.user,
            widget=widget,
            defaults={"is_visible": widget.default_visible, "position": 999},
        )

        if "is_visible" in request.data:
            pref.is_visible = bool(request.data["is_visible"])
        if "position" in request.data:
            pref.position = int(request.data["position"])
        pref.save()

        return Response({"detail": "Preferencia guardada."})
