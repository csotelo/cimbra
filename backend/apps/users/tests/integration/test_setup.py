"""Integration tests for US01 — Fundación y setup del proyecto.

Verifica los 4 criterios de aceptación del feature file usando las URLs
exactas especificadas en acceptance.feature (/api/auth/...).

Estado esperado: todos en RED porque las URLs /api/auth/ no están registradas
(el código actual usa /api/users/). El developer deberá agregar el prefijo
/api/auth/ en config/urls.py.
"""

import pytest
from django.test import TestCase
from rest_framework.test import APIClient


class TestCA01AdminRespondsWithoutError(TestCase):
    """CA01 — Django admin responde sin error (status 200)."""

    def setUp(self):
        self.client = APIClient()

    def test_admin_endpoint_returns_200(self):
        """GET /admin/ debe retornar 200 (siguiendo el redirect a /admin/login/).

        Django admin redirige unauthenticated requests a /admin/login/ (302).
        Con follow=True el redirect se sigue y el login page retorna 200.
        """
        response = self.client.get("/admin/", follow=True)
        self.assertEqual(response.status_code, 200)


class TestCA02RegisterAcceptsEmail(TestCase):
    """CA02 — API acepta email como identificador en el registro."""

    def setUp(self):
        self.client = APIClient()

    def test_register_endpoint_returns_201_with_email_field(self):
        """POST /api/auth/register/ con email válido debe retornar 201 y campo email.

        RED por dos razones:
        1. La URL /api/auth/register/ no existe → 404 (existe /api/users/register/).
        2. El endpoint actual retorna {"detail": ...} sin campo "email".
        """
        response = self.client.post(
            "/api/auth/register/",
            {"email": "setup-test@atf.com", "password": "TestPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("email", response.data)
        self.assertEqual(response.data["email"], "setup-test@atf.com")

    def test_register_endpoint_rejects_invalid_email(self):
        """POST /api/auth/register/ con email inválido debe retornar 400.

        RED: /api/auth/register/ no existe → 404.
        """
        response = self.client.post(
            "/api/auth/register/",
            {"email": "not-an-email", "password": "TestPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class TestCA03PostgresAccessible(TestCase):
    """CA03 — Docker Compose — PostgreSQL accesible (Django no devuelve 500)."""

    def setUp(self):
        self.client = APIClient()

    def test_login_get_returns_405_confirming_db_accessible(self):
        """GET /api/auth/login/ debe retornar 405 (método no permitido, no 500).

        Un 405 confirma que Django está conectado a la DB sin errores.
        RED: /api/auth/login/ no existe → 404 (existe /api/users/login/).
        """
        response = self.client.get("/api/auth/login/")
        self.assertEqual(response.status_code, 405)


@pytest.mark.django_db
class TestCA04LoginWithEmailReturnsTenantList(TestCase):
    """CA04 — CustomUser usa email como identificador (no username)."""

    def setUp(self):
        self.client = APIClient()
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(
            email="admin@example.com",
            password="admin123",
        )

    def test_login_with_email_returns_200_and_tenant_list(self):
        """POST /api/auth/login/ con email/password válidos debe retornar 200 y tenant_list.

        RED: /api/auth/login/ no existe → 404 (existe /api/users/login/).
        """
        response = self.client.post(
            "/api/auth/login/",
            {"email": "admin@example.com", "password": "admin123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("tenant_list", response.data)

    def test_login_with_username_fails(self):
        """POST /api/auth/login/ con username (no email) debe retornar 400 o 401.

        Verifica que el sistema no acepta 'username' como identificador.
        RED: /api/auth/login/ no existe → 404.
        """
        response = self.client.post(
            "/api/auth/login/",
            {"username": "admin@example.com", "password": "admin123"},
            format="json",
        )
        self.assertIn(response.status_code, [400, 401])
