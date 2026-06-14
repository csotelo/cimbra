"""Pytest configuration for Django tests."""

import os
import sys

import django
from django.conf import settings


def pytest_configure():
    """Configure Django settings for tests."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    if not settings.configured:
        django.setup()


def pytest_collection_modifyitems(items):
    """Add django marker to all Django tests."""
    import pytest

    for item in items:
        if "django" not in item.keywords:
            item.add_marker(pytest.mark.django)
