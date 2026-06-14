"""Unit tests — US13: slug auto-generado al crear tenant en el admin."""

import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from apps.tenants.admin import TenantAdmin
from apps.tenants.models import Tenant
from apps.tenants.utils import generate_unique_slug  # noqa: F401 — módulo no existe aún


@pytest.fixture
def site():
    return AdminSite()


@pytest.fixture
def tenant_admin(site):
    return TenantAdmin(Tenant, site)


@pytest.fixture
def rf():
    return RequestFactory()


class TestTenantAdminSlugFieldExcluded:
    """CA1: el formulario de creación no muestra el campo slug."""

    def test_add_form_fields_do_not_include_slug(self, tenant_admin, rf):
        """El form generado por get_form() no debe contener el campo slug."""
        request = rf.get("/admin/tenants/tenant/add/")
        form_class = tenant_admin.get_form(request, obj=None)
        assert "slug" not in form_class().fields

    def test_add_fieldsets_do_not_list_slug(self, tenant_admin, rf):
        """Ningún fieldset del formulario de alta debe declarar el campo slug."""
        request = rf.get("/admin/tenants/tenant/add/")
        all_fieldset_fields = [
            field
            for _, opts in tenant_admin.get_fieldsets(request, obj=None)
            for field in opts.get("fields", [])
        ]
        assert "slug" not in all_fieldset_fields


@pytest.mark.django_db
class TestGenerateUniqueSlug:
    """CA2: el slug se genera automáticamente a partir del nombre."""

    def test_plain_name_produces_hyphenated_lowercase_slug(self):
        """Nombre simple → slug en minúsculas con guiones."""
        slug = generate_unique_slug("Acme Corp", Tenant)
        assert slug == "acme-corp"

    def test_name_with_accents_produces_ascii_slug(self):
        """Nombre con tildes → slug ASCII sin caracteres especiales."""
        slug = generate_unique_slug("Café del Mar", Tenant)
        assert slug.startswith("cafe")

    def test_name_with_extra_spaces_is_normalized(self):
        """Espacios múltiples o bordes se normalizan en el slug."""
        slug = generate_unique_slug("  Mi   Empresa  ", Tenant)
        assert slug == "mi-empresa"

    def test_name_with_numbers_preserves_digits(self):
        """Los dígitos en el nombre se conservan en el slug."""
        slug = generate_unique_slug("Empresa 2025", Tenant)
        assert slug == "empresa-2025"


@pytest.mark.django_db
class TestGenerateUniqueSlugUniqueness:
    """CA3: si el slug ya existe se añade sufijo numérico."""

    def test_existing_slug_receives_suffix_2(self):
        """Cuando el slug ya existe, el siguiente recibe -2."""
        Tenant.objects.create(name="Acme Corp", slug="acme-corp", max_users=5)
        slug = generate_unique_slug("Acme Corp", Tenant)
        assert slug == "acme-corp-2"

    def test_multiple_existing_slugs_increment_suffix_correctly(self):
        """Los sufijos se incrementan sin colisiones cuando hay varios duplicados."""
        Tenant.objects.create(name="Tenant A", slug="tenant-a", max_users=5)
        Tenant.objects.create(name="Tenant A2", slug="tenant-a-2", max_users=5)
        slug = generate_unique_slug("Tenant A", Tenant)
        assert slug == "tenant-a-3"

    def test_unique_name_does_not_receive_suffix(self):
        """Un nombre sin duplicado produce slug sin sufijo."""
        slug = generate_unique_slug("Nombre Absolutamente Único XYZ", Tenant)
        assert slug == "nombre-absolutamente-unico-xyz"
