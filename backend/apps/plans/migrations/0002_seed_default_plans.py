"""Seed default plans: Free, Basic, Pro, Enterprise."""

from django.db import migrations


PLANS = [
    {
        "name": "Free",
        "description": "Plan gratuito para explorar la plataforma.",
        "is_default": True,
        "is_active": True,
        "max_tenants": 1,
        "rate_limit_per_minute": 30,
        "requests_per_hour": 500,
        "requests_per_day": 2_000,
    },
    {
        "name": "Basic",
        "description": "Plan básico para equipos pequeños.",
        "is_default": False,
        "is_active": True,
        "max_tenants": 3,
        "rate_limit_per_minute": 60,
        "requests_per_hour": 2_000,
        "requests_per_day": 20_000,
    },
    {
        "name": "Pro",
        "description": "Plan profesional para empresas en crecimiento.",
        "is_default": False,
        "is_active": True,
        "max_tenants": 10,
        "rate_limit_per_minute": 120,
        "requests_per_hour": 10_000,
        "requests_per_day": 100_000,
    },
    {
        "name": "Enterprise",
        "description": "Plan empresarial sin límites prácticos.",
        "is_default": False,
        "is_active": True,
        "max_tenants": 100,
        "rate_limit_per_minute": 600,
        "requests_per_hour": 100_000,
        "requests_per_day": 1_000_000,
    },
]


def seed_plans(apps, schema_editor):
    Plan = apps.get_model("plans", "Plan")
    UserSubscription = apps.get_model("plans", "UserSubscription")
    User = apps.get_model("users", "CustomUser")

    for data in PLANS:
        Plan.objects.get_or_create(name=data["name"], defaults=data)

    # Assign Free plan to the default admin if not already subscribed
    free_plan = Plan.objects.filter(name="Free").first()
    if not free_plan:
        return

    admin = User.objects.filter(is_superuser=True).first()
    if admin and not UserSubscription.objects.filter(user=admin, valid_to__isnull=True).exists():
        UserSubscription.objects.create(user=admin, plan=free_plan)


def unseed_plans(apps, schema_editor):
    Plan = apps.get_model("plans", "Plan")
    Plan.objects.filter(name__in=[p["name"] for p in PLANS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("plans", "0001_initial"),
        ("users", "0002_create_default_admin"),
    ]

    operations = [
        migrations.RunPython(seed_plans, unseed_plans),
    ]
