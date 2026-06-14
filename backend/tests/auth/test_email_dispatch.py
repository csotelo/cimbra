"""Integration tests for Celery email dispatch tasks — US10.

These tests call the Celery tasks directly (not via HTTP) to isolate
template-resolution failures from endpoint logic.

With CELERY_TASK_ALWAYS_EAGER=True (testing.py) the tasks execute
synchronously, so TemplateDoesNotExist surfaces immediately.

Expected RED state (container): tasks raise TemplateDoesNotExist
because the email templates are not found at the path Django resolves.
"""

import pytest
from django.core import mail
from django.template.exceptions import TemplateDoesNotExist

from apps.users.tasks import send_email_verification, send_password_reset


@pytest.mark.django_db
class TestSendEmailVerificationTask:
    """send_email_verification task must render templates without error."""

    def test_task_renders_templates_and_sends_email(self):
        """Task completes without TemplateDoesNotExist and places email in outbox."""
        from apps.users.models import CustomUser

        user = CustomUser.objects.create_user(
            email="us10verify@example.com",
            password="Secret123!",
        )
        token = "test-verification-token-us10"

        send_email_verification(user.id, token)

        assert len(mail.outbox) == 1
        sent = mail.outbox[0]
        assert sent.to == ["us10verify@example.com"]
        assert "Verify" in sent.subject

    def test_task_email_body_contains_verification_url(self):
        """Email body must contain the verification URL built from the token."""
        from apps.users.models import CustomUser

        user = CustomUser.objects.create_user(
            email="us10verify2@example.com",
            password="Secret123!",
        )
        token = "unique-token-us10-verify"

        send_email_verification(user.id, token)

        assert len(mail.outbox) == 1
        assert token in mail.outbox[0].body

    def test_task_sends_html_alternative(self):
        """Email must include an HTML alternative part (renders html template)."""
        from apps.users.models import CustomUser

        user = CustomUser.objects.create_user(
            email="us10verify3@example.com",
            password="Secret123!",
        )
        token = "html-token-us10"

        send_email_verification(user.id, token)

        assert len(mail.outbox) == 1
        alternatives = mail.outbox[0].alternatives
        assert alternatives, "No HTML alternative attached — html template not rendered"
        content_types = [ct for _, ct in alternatives]
        assert "text/html" in content_types


@pytest.mark.django_db
class TestSendPasswordResetTask:
    """send_password_reset task must render templates without error."""

    def test_task_renders_templates_and_sends_email(self):
        """Task completes without TemplateDoesNotExist and places email in outbox."""
        from apps.users.models import CustomUser

        user = CustomUser.objects.create_user(
            email="us10reset@example.com",
            password="Secret123!",
        )
        token = "test-reset-token-us10"

        send_password_reset(user.id, token)

        assert len(mail.outbox) == 1
        sent = mail.outbox[0]
        assert sent.to == ["us10reset@example.com"]
        assert "Reset" in sent.subject

    def test_task_email_body_contains_reset_url(self):
        """Email body must contain the reset URL built from the token."""
        from apps.users.models import CustomUser

        user = CustomUser.objects.create_user(
            email="us10reset2@example.com",
            password="Secret123!",
        )
        token = "unique-token-us10-reset"

        send_password_reset(user.id, token)

        assert len(mail.outbox) == 1
        assert token in mail.outbox[0].body

    def test_task_sends_html_alternative(self):
        """Email must include an HTML alternative part (renders html template)."""
        from apps.users.models import CustomUser

        user = CustomUser.objects.create_user(
            email="us10reset3@example.com",
            password="Secret123!",
        )
        token = "html-reset-token-us10"

        send_password_reset(user.id, token)

        assert len(mail.outbox) == 1
        alternatives = mail.outbox[0].alternatives
        assert alternatives, "No HTML alternative attached — html template not rendered"
        content_types = [ct for _, ct in alternatives]
        assert "text/html" in content_types
