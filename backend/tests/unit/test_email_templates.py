"""Unit tests for email template resolution — US10.

These tests verify that all four email templates are resolvable by Django's
template engine regardless of whether the app runs on the host or inside the
Docker container.

Expected RED state (container): render_to_string raises TemplateDoesNotExist
because BASE_DIR resolves to '/' and TEMPLATES[0]['DIRS'] = ['/templates'],
while the volume mounts the templates at '/app/templates/'.
"""

import os
from pathlib import Path

import pytest
from django.conf import settings
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string


VERIFY_EMAIL_CONTEXT = {
    "user_email": "us10test@example.com",
    "verify_url": "http://localhost:3000/verify-email/?token=abc123",
    "frontend_url": "http://localhost:3000",
}

PASSWORD_RESET_CONTEXT = {
    "user_email": "us10test@example.com",
    "reset_url": "http://localhost:3000/reset-password/?token=abc123",
    "frontend_url": "http://localhost:3000",
}


class TestEmailTemplateResolution:
    """Verify that all email templates are resolvable by Django."""

    def test_verify_email_txt_template_is_resolvable(self):
        """render_to_string must not raise TemplateDoesNotExist for verify_email.txt."""
        result = render_to_string("emails/verify_email.txt", VERIFY_EMAIL_CONTEXT)
        assert "us10test@example.com" in result

    def test_verify_email_html_template_is_resolvable(self):
        """render_to_string must not raise TemplateDoesNotExist for verify_email.html."""
        result = render_to_string("emails/verify_email.html", VERIFY_EMAIL_CONTEXT)
        assert "us10test@example.com" in result

    def test_password_reset_txt_template_is_resolvable(self):
        """render_to_string must not raise TemplateDoesNotExist for password_reset.txt."""
        result = render_to_string("emails/password_reset.txt", PASSWORD_RESET_CONTEXT)
        assert "us10test@example.com" in result

    def test_password_reset_html_template_is_resolvable(self):
        """render_to_string must not raise TemplateDoesNotExist for password_reset.html."""
        result = render_to_string("emails/password_reset.html", PASSWORD_RESET_CONTEXT)
        assert "us10test@example.com" in result


class TestTemplateDirsConfiguration:
    """Verify that settings.TEMPLATES[0]['DIRS'] resolves to an existing path."""

    def test_templates_dirs_contains_at_least_one_existing_path(self):
        """At least one TEMPLATES DIR must exist on the filesystem."""
        template_config = settings.TEMPLATES[0]
        dirs = template_config.get("DIRS", [])
        existing = [str(d) for d in dirs if Path(d).exists()]
        assert existing, (
            f"None of the TEMPLATES[0]['DIRS'] exist on the filesystem: {dirs}. "
            f"Inside Docker the volume mounts templates at /app/templates but "
            f"BASE_DIR resolves to '/', making DIRS=['/templates'] which does not exist."
        )

    def test_email_templates_subdir_is_reachable_from_dirs(self):
        """The emails/ subdirectory must exist under one of the TEMPLATES DIRs."""
        template_config = settings.TEMPLATES[0]
        dirs = template_config.get("DIRS", [])
        email_dirs_found = [
            str(d / "emails") for d in dirs if (Path(d) / "emails").exists()
        ]
        assert email_dirs_found, (
            f"No 'emails/' subdirectory found under any TEMPLATES[0]['DIRS']: {dirs}"
        )

    def test_all_four_email_template_files_exist_on_disk(self):
        """All four email template files must be present on the filesystem."""
        template_config = settings.TEMPLATES[0]
        dirs = template_config.get("DIRS", [])

        expected = [
            "emails/verify_email.txt",
            "emails/verify_email.html",
            "emails/password_reset.txt",
            "emails/password_reset.html",
        ]
        missing = []
        for template_name in expected:
            found = any((Path(d) / template_name).exists() for d in dirs)
            if not found:
                missing.append(template_name)

        assert not missing, (
            f"Email template files not found in any TEMPLATES DIR {dirs}: {missing}"
        )
