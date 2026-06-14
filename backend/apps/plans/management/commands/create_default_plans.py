"""Management command to seed default subscription plans."""

from django.core.management.base import BaseCommand

from apps.plans.models import Plan


PLANS = [
    {
        "name": "Free",
        "description": "Plan gratuito para explorar la plataforma.",
        "is_default": True,
        "max_tenants": 1,
        "rate_limit_per_minute": 30,
        "requests_per_hour": 500,
        "requests_per_day": 2_000,
    },
    {
        "name": "Basic",
        "description": "Plan básico para proyectos pequeños.",
        "is_default": False,
        "max_tenants": 3,
        "rate_limit_per_minute": 60,
        "requests_per_hour": 2_000,
        "requests_per_day": 20_000,
    },
    {
        "name": "Pro",
        "description": "Plan profesional para equipos.",
        "is_default": False,
        "max_tenants": 10,
        "rate_limit_per_minute": 200,
        "requests_per_hour": 10_000,
        "requests_per_day": 100_000,
    },
    {
        "name": "Enterprise",
        "description": "Plan enterprise sin restricciones prácticas.",
        "is_default": False,
        "max_tenants": 100,
        "rate_limit_per_minute": 1_000,
        "requests_per_hour": 100_000,
        "requests_per_day": 1_000_000,
    },
]


class Command(BaseCommand):
    help = "Creates default subscription plans (Free, Basic, Pro, Enterprise)."

    def handle(self, *args, **options):
        created = 0
        for data in PLANS:
            plan, is_new = Plan.objects.update_or_create(
                name=data["name"],
                defaults=data,
            )
            if is_new:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"  Created: {plan.name}"))
            else:
                self.stdout.write(f"  Exists:  {plan.name}")

        self.stdout.write(self.style.SUCCESS(f"\nDone — {created} plan(s) created."))
