"""Integration tests — US13: slug auto-generado al crear tenant en el admin."""

import pytest
from django.urls import reverse

from apps.tenants.models import Tenant
from apps.users.models import CustomUser


@pytest.fixture
def superadmin(db):
    return CustomUser.objects.create_superuser(
        email="superadmin@test.com",
        password="Admin123!",
    )


@pytest.fixture
def admin_client(client, superadmin):
    client.force_login(superadmin)
    return client


@pytest.mark.django_db
class TestAdminTenantAddSlugExcluded:
    """CA1: el formulario de alta no muestra el campo slug en el HTML."""

    def test_admin_add_page_does_not_render_slug_input(self, admin_client):
        """GET al formulario de alta no debe contener <input name="slug">."""
        url = reverse("admin:tenants_tenant_add")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert b'name="slug"' not in response.content


@pytest.mark.django_db
class TestAdminTenantCreateAutoSlug:
    """CA2 + CA3: el slug se genera y es único al guardar desde el admin."""

    def test_create_tenant_without_slug_field_redirects_on_success(self, admin_client):
        """POST al formulario de alta sin enviar slug debe redirigir (creación exitosa)."""
        url = reverse("admin:tenants_tenant_add")
        response = admin_client.post(
            url,
            {
                "name": "Nuevo Tenant",
                "is_active": "on",
                "max_users": 10,
                "rate_limit": 100,
                "_save": "Save",
            },
        )
        assert response.status_code == 302

    def test_created_tenant_has_slug_derived_from_name(self, admin_client):
        """El tenant guardado desde el admin debe tener slug generado a partir del nombre."""
        url = reverse("admin:tenants_tenant_add")
        admin_client.post(
            url,
            {
                "name": "Mi Empresa",
                "is_active": "on",
                "max_users": 10,
                "rate_limit": 100,
                "_save": "Save",
            },
        )
        tenant = Tenant.objects.get(name="Mi Empresa")
        assert tenant.slug == "mi-empresa"

    def test_duplicate_name_creates_tenant_with_unique_slug(self, admin_client):
        """Crear un segundo tenant con el mismo nombre produce un slug con sufijo único."""
        Tenant.objects.create(name="Empresa ABC", slug="empresa-abc", max_users=10)
        url = reverse("admin:tenants_tenant_add")
        admin_client.post(
            url,
            {
                "name": "Empresa ABC",
                "is_active": "on",
                "max_users": 10,
                "rate_limit": 100,
                "_save": "Save",
            },
        )
        assert Tenant.objects.filter(name="Empresa ABC").count() == 2
        new_tenant = (
            Tenant.objects.filter(name="Empresa ABC").order_by("-created_at").first()
        )
        assert new_tenant.slug != "empresa-abc"
        assert new_tenant.slug.startswith("empresa-abc")
