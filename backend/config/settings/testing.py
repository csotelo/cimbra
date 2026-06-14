"""Test settings - uses SQLite for fast local testing."""

import os

from .base import *  # noqa: F401,F403

SECRET_KEY = "test-secret-key-not-for-production"  # noqa: F405

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Skip migrations for tests - create tables directly from models
MIGRATION_MODULES = {
    "users": None,
    "tenants": None,
    "api_tokens": None,
    "notifications": None,
    "admin": None,
    "auth": None,
    "contenttypes": None,
    "sessions": None,
    "django_celery_beat": None,
}
