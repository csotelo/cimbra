import os
from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_default_admin(apps, schema_editor):
    User = apps.get_model("users", "CustomUser")
    email = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@ximbra.local")
    password = os.environ.get("DEFAULT_ADMIN_PASSWORD", "P4ssw0rd!")
    if not User.objects.filter(is_superuser=True).exists():
        User.objects.create(
            email=email,
            password=make_password(password),
            is_superuser=True,
            is_staff=True,
            is_active=True,
            is_email_verified=True,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_admin, migrations.RunPython.noop),
    ]
