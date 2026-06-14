"""Signals for automatic plan assignment on user registration."""

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


@receiver(post_save, sender=User)
def assign_default_plan(sender, instance, created, **kwargs):
    """Auto-assign the default plan when a new user is created."""
    if not created:
        return
    try:
        from apps.plans.models import Plan, UserSubscription

        default_plan = Plan.objects.filter(is_default=True, is_active=True).first()
        if default_plan:
            UserSubscription.objects.create(user=instance, plan=default_plan)
    except Exception:
        pass  # Never block registration if plans are misconfigured
