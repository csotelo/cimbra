"""Views for field operations: employees, projects, geo-fences, mobile refuges and live tracking."""

import json
import os

import redis as _redis_lib
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.middleware import get_current_tenant
from apps.tenants.permissions import IsTenantMember, IsTenantAdmin

from .models import Employee, GeoFence, MobileRefuge, Project, RefugePoint
from .serializers import (
    EmployeeSerializer,
    GeoFenceGeoSerializer,
    GeoFenceSerializer,
    MobileRefugeSerializer,
    ProjectSerializer,
    RefugePointGeoSerializer,
    RefugePointSerializer,
)

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = _redis_lib.Redis.from_url(
            os.environ.get("REDIS_URL", "redis://redis:6379"),
            decode_responses=True,
        )
    return _redis_client


class EmployeeViewSet(viewsets.ModelViewSet):
    """CRUD for field employees scoped to the active tenant."""

    permission_classes = [IsAuthenticated, IsTenantMember]
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        tenant = get_current_tenant()
        if not tenant:
            return Employee.objects.none()
        qs = Employee.objects.filter(tenant=tenant)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(full_name__icontains=search)
        return qs

    def perform_create(self, serializer):
        tenant = get_current_tenant()
        serializer.save(tenant=tenant)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsTenantAdmin])
    def toggle(self, request, pk=None):
        """Toggle employee active status."""
        employee = self.get_object()
        employee.is_active = not employee.is_active
        employee.save(update_fields=["is_active"])
        return Response({"id": str(employee.id), "is_active": employee.is_active})


class ProjectViewSet(viewsets.ModelViewSet):
    """CRUD for field projects scoped to the active tenant."""

    permission_classes = [IsAuthenticated, IsTenantMember]
    serializer_class = ProjectSerializer

    def get_queryset(self):
        tenant = get_current_tenant()
        if not tenant:
            return Project.objects.none()
        qs = Project.objects.filter(tenant=tenant).prefetch_related("employees")
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        return qs

    def perform_create(self, serializer):
        tenant = get_current_tenant()
        serializer.save(tenant=tenant)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsTenantAdmin])
    def toggle(self, request, pk=None):
        """Toggle project active status."""
        project = self.get_object()
        project.is_active = not project.is_active
        project.save(update_fields=["is_active"])
        return Response({"id": str(project.id), "is_active": project.is_active})

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsTenantAdmin])
    def assign_employees(self, request, pk=None):
        """Replace the employee M2M list for this project."""
        project = self.get_object()
        tenant = get_current_tenant()
        ids = request.data.get("employee_ids", [])
        employees = Employee.objects.filter(id__in=ids, tenant=tenant, is_active=True)
        project.employees.set(employees)
        return Response({"assigned": [str(e.id) for e in employees]})


class GeoFenceViewSet(viewsets.ModelViewSet):
    """CRUD for geo-fences (work fronts) scoped to the active tenant."""

    permission_classes = [IsAuthenticated, IsTenantMember]
    serializer_class = GeoFenceSerializer

    def get_queryset(self):
        tenant = get_current_tenant()
        if not tenant:
            return GeoFence.objects.none()
        qs = GeoFence.objects.filter(tenant=tenant).select_related("project")
        project_id = self.request.query_params.get("project")
        if project_id:
            qs = qs.filter(project_id=project_id)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        return qs

    def perform_create(self, serializer):
        tenant = get_current_tenant()
        project = serializer.validated_data["project"]
        if project.tenant != tenant:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("El proyecto no pertenece al tenant activo.")
        serializer.save(tenant=tenant)

    @action(detail=False, methods=["get"])
    def geojson(self, request):
        """GeoJSON FeatureCollection of active geo-fences for Leaflet."""
        qs = self.get_queryset().filter(is_active=True)
        serializer = GeoFenceGeoSerializer(qs, many=True)
        return Response(serializer.data)


class MobileRefugeViewSet(viewsets.ModelViewSet):
    """CRUD for mobile refuge units scoped to the active tenant."""

    permission_classes = [IsAuthenticated, IsTenantMember]
    serializer_class = MobileRefugeSerializer

    def get_queryset(self):
        tenant = get_current_tenant()
        if not tenant:
            return MobileRefuge.objects.none()
        qs = MobileRefuge.objects.filter(tenant=tenant).select_related("conductor", "project")
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        return qs

    def perform_create(self, serializer):
        tenant = get_current_tenant()
        serializer.save(tenant=tenant)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsTenantAdmin])
    def toggle(self, request, pk=None):
        obj = self.get_object()
        obj.is_active = not obj.is_active
        obj.save(update_fields=["is_active"])
        return Response({"id": str(obj.id), "is_active": obj.is_active})


class RefugePointViewSet(viewsets.ModelViewSet):
    """CRUD for fixed refuge points scoped to the active tenant."""

    permission_classes = [IsAuthenticated, IsTenantMember]
    serializer_class = RefugePointSerializer

    def get_queryset(self):
        tenant = get_current_tenant()
        if not tenant:
            return RefugePoint.objects.none()
        qs = RefugePoint.objects.filter(tenant=tenant).select_related("project")
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        project_id = self.request.query_params.get("project")
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs

    def perform_create(self, serializer):
        tenant = get_current_tenant()
        serializer.save(tenant=tenant)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsTenantAdmin])
    def toggle(self, request, pk=None):
        obj = self.get_object()
        obj.is_active = not obj.is_active
        obj.save(update_fields=["is_active"])
        return Response({"id": str(obj.id), "is_active": obj.is_active})

    @action(detail=False, methods=["get"])
    def geojson(self, request):
        """GeoJSON FeatureCollection of active refuge points for Leaflet."""
        qs = self.get_queryset().filter(is_active=True)
        serializer = RefugePointGeoSerializer(qs, many=True)
        return Response(serializer.data)


class TrackingLiveView(APIView):
    """Read live positions from Redis for all field entities in the active tenant."""

    permission_classes = [IsAuthenticated, IsTenantMember]

    def get(self, request):
        tenant = get_current_tenant()
        if not tenant:
            return Response({"positions": []})

        r = _get_redis()

        raw = r.hgetall(f"tracking:last_position:{tenant.id}")

        employee_ids = []
        positions = []
        for _field, value_str in raw.items():
            try:
                data = json.loads(value_str)
                # Normalise entity_id from the hash field if missing in payload
                if "entity_id" not in data:
                    data["entity_id"] = _field.split(":", 1)[-1]
                if "entity_type" not in data:
                    data["entity_type"] = _field.split(":", 1)[0]
                positions.append(data)
                if data.get("entity_type") == "employee":
                    employee_ids.append(data["entity_id"])
            except Exception:
                continue

        # Enrich with employee names
        emp_map = {
            str(e.id): e.full_name
            for e in Employee.objects.filter(id__in=employee_ids, tenant=tenant)
        }

        # Map conductor → mobile refuge
        refuges = (
            MobileRefuge.objects.filter(tenant=tenant, is_active=True, conductor__isnull=False)
            .select_related("conductor")
        )
        conductor_to_refuge = {str(ref.conductor_id): ref for ref in refuges}

        for pos in positions:
            eid = pos.get("entity_id", "")
            pos["label"] = emp_map.get(eid, "Desconocido")
            if eid in conductor_to_refuge:
                ref = conductor_to_refuge[eid]
                pos["mobile_refuge"] = {
                    "id": str(ref.id),
                    "code": ref.code,
                    "plate": ref.plate,
                    "capacity": ref.capacity,
                }
            else:
                pos["mobile_refuge"] = None

            # Enrich with field alert level (set by check_field_alerts Celery task)
            raw_alert = r.get(f"tracking:field_alert:{eid}")
            if raw_alert:
                try:
                    pos["field_alert"] = json.loads(raw_alert)
                except Exception:
                    pos["field_alert"] = None
            else:
                pos["field_alert"] = None

        return Response({"positions": positions})
