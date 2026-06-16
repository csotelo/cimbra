"""Views for field operations: employees, projects, geo-fences."""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.middleware import get_current_tenant
from apps.tenants.permissions import IsTenantMember, IsTenantAdmin

from .models import Employee, GeoFence, Project
from .serializers import (
    EmployeeSerializer,
    GeoFenceGeoSerializer,
    GeoFenceSerializer,
    ProjectSerializer,
)


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
