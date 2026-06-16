"""Base settings - shared across all environments."""

import os
import urllib.parse as _urlparse
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-change-in-production")

DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "corsheaders",
    "rest_framework",
    "rest_framework_gis",
    "rest_framework_simplejwt",
    "django_celery_beat",
    "channels",
    "storages",
    "core.apps.CoreConfig",
    "apps.users.apps.UsersConfig",
    "apps.tenants.apps.TenantsConfig",
    "apps.api_tokens.apps.ApiTokensConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.jobs.apps.JobsConfig",
    "apps.plans.apps.PlansConfig",
    "apps.dashboard.apps.DashboardConfig",
    "apps.watchdog.apps.WatchdogConfig",
    "apps.weather.apps.WeatherConfig",
    "apps.field.apps.FieldConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.TenantMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("POSTGRES_DB", "multitenant_db"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "postgres"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ── Object Storage (MinIO en dev / AWS S3 en prod) ────────────────────────────
# En desarrollo: docker-compose levanta MinIO en localhost:9000
# En producción: eliminar AWS_S3_ENDPOINT_URL y apuntar a AWS S3 real
_AWS_ENDPOINT = os.environ.get("AWS_S3_ENDPOINT_URL")

if os.environ.get("AWS_ACCESS_KEY_ID"):
    DEFAULT_FILE_STORAGE  = "storages.backends.s3boto3.S3Boto3Storage"
    STATICFILES_STORAGE   = "storages.backends.s3boto3.S3StaticStorage"

    AWS_ACCESS_KEY_ID       = os.environ["AWS_ACCESS_KEY_ID"]
    AWS_SECRET_ACCESS_KEY   = os.environ["AWS_SECRET_ACCESS_KEY"]
    AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "ximbra")
    AWS_S3_REGION_NAME      = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")
    AWS_DEFAULT_ACL         = None
    AWS_S3_FILE_OVERWRITE   = False
    AWS_QUERYSTRING_AUTH    = False   # URLs públicas sin firma (ajustar en prod si privadas)

    if _AWS_ENDPOINT:
        # MinIO o cualquier S3-compatible local
        AWS_S3_ENDPOINT_URL          = _AWS_ENDPOINT
        AWS_S3_ADDRESSING_STYLE      = "path"   # MinIO requiere path style
        AWS_S3_USE_SSL               = _AWS_ENDPOINT.startswith("https")

    MEDIA_URL = f"{_AWS_ENDPOINT or 'https://s3.amazonaws.com'}/{AWS_STORAGE_BUCKET_NAME}/media/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "users.CustomUser"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "core.authentication.JWTCookieAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

_REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")
_redis = _urlparse.urlparse(_REDIS_URL)
_redis_host = {"host": _redis.hostname or "redis", "port": _redis.port or 6379}
if _redis.password:
    _redis_host["password"] = _redis.password

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", f"{_REDIS_URL}/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", f"{_REDIS_URL}/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_TRACK_STARTED = True

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [_redis_host]},
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"{_REDIS_URL}/1",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.example.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@example.com")

CELERY_BEAT_SCHEDULE = {
    "send-heartbeat-ping": {
        "task": "apps.watchdog.tasks.send_heartbeat_ping",
        "schedule": 30.0,
    },
    "notify-storm-alerts": {
        "task": "weather.notify_pending_alerts",
        "schedule": 600.0,  # cada 10 minutos
    },
}

MAX_TENANTS_PER_USER = 5
API_TOKEN_EXPIRY_DAYS = 365
JWT_API_TOKEN_SECRET = os.environ.get("FASTAPI_SECRET_KEY", "dev-only-not-for-production")

ALLOW_SELF_REGISTRATION = True
EMAIL_VERIFICATION_EXPIRY_HOURS = 24
PASSWORD_RESET_EXPIRY_HOURS = 1
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

SINGLE_TENANT_MODE = os.environ.get("SINGLE_TENANT_MODE", "True") == "True"
MAIN_TENANT_SLUG = os.environ.get("MAIN_TENANT_SLUG", "ximbra")

CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if o.strip()
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False
CORS_EXPOSE_HEADERS = ["Content-Type", "X-CSRFToken"]

CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = not DEBUG
X_FRAME_OPTIONS = "DENY"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
