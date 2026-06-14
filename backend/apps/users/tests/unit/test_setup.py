"""Unit tests for US01 — Fundación y setup del proyecto.

Verifica que CustomUser está configurado con email como identificador,
sin campo username, y con hashing correcto de contraseñas.
"""

import pytest
from django.contrib.auth import get_user_model


CustomUser = get_user_model()


class TestCustomUserModelConfiguration:
    """CA04 (parcial) — CustomUser usa email como identificador, no username."""

    def test_custom_user_uses_email_as_username_field(self):
        """USERNAME_FIELD debe ser 'email', no 'username'."""
        assert CustomUser.USERNAME_FIELD == "email"

    def test_custom_user_required_fields_does_not_include_username(self):
        """REQUIRED_FIELDS no debe incluir username."""
        assert "username" not in CustomUser.REQUIRED_FIELDS

    def test_custom_user_has_no_username_attribute(self):
        """El modelo no debe tener campo 'username'."""
        assert not hasattr(CustomUser, "username")

    @pytest.mark.django_db
    def test_create_user_requires_email(self):
        """create_user sin email debe lanzar ValueError."""
        with pytest.raises(ValueError):
            CustomUser.objects.create_user(email=None, password="TestPass123!")

    @pytest.mark.django_db
    def test_create_user_hashes_password(self):
        """La contraseña almacenada no debe ser igual al texto plano."""
        user = CustomUser.objects.create_user(
            email="hash-test@atf.com",
            password="TestPass123!",
        )
        assert user.password != "TestPass123!"

    @pytest.mark.django_db
    def test_custom_user_str_returns_email(self):
        """__str__ debe retornar el email del usuario."""
        user = CustomUser.objects.create_user(
            email="str-test@atf.com",
            password="TestPass123!",
        )
        assert str(user) == "str-test@atf.com"

    @pytest.mark.django_db
    def test_create_user_sets_is_email_verified_false_by_default(self):
        """Un usuario nuevo no debe tener email verificado por defecto."""
        user = CustomUser.objects.create_user(
            email="unverified@atf.com",
            password="TestPass123!",
        )
        assert user.is_email_verified is False
