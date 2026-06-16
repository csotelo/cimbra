"""Serializers for field operations."""

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import Employee, GeoFence, Project


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = [
            "id", "full_name", "document_number", "device_id",
            "fcm_token", "photo", "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_device_id(self, value):
        qs = Employee.objects.filter(device_id=value)
        instance = self.instance
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Este código de dispositivo ya está registrado.")
        return value


class ProjectSerializer(serializers.ModelSerializer):
    employee_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Employee.objects.none(),
        source="employees",
        required=False,
    )
    employee_count = serializers.SerializerMethodField()
    employees_detail = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id", "name", "description", "start_date", "end_date",
            "is_active", "created_at", "employee_ids", "employee_count", "employees_detail",
        ]
        read_only_fields = ["id", "created_at", "employee_count", "employees_detail"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request:
            from core.middleware import get_current_tenant
            tenant = get_current_tenant()
            if tenant:
                self.fields["employee_ids"].child_relation.queryset = Employee.objects.filter(
                    tenant=tenant, is_active=True
                )

    def get_employee_count(self, obj):
        return obj.employees.count()

    def get_employees_detail(self, obj):
        return [
            {"id": str(e.id), "full_name": e.full_name, "document_number": e.document_number}
            for e in obj.employees.filter(is_active=True)
        ]


class GeoFenceSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = GeoFence
        fields = [
            "id", "project", "project_name", "name",
            "perimeter", "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at", "project_name"]


class GeoFenceGeoSerializer(GeoFeatureModelSerializer):
    """GeoJSON FeatureCollection of active geo-fences for Leaflet overlay."""

    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = GeoFence
        geo_field = "perimeter"
        fields = ["id", "name", "project", "project_name", "is_active"]
