import os
from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_default_admin(apps, schema_editor):
    email = os.environ.get("DEFAULT_ADMIN_EMAIL")
    password = os.environ.get("DEFAULT_ADMIN_PASSWORD")
    if not email or not password:
        # Requiere DEFAULT_ADMIN_EMAIL y DEFAULT_ADMIN_PASSWORD en .env
        # Sin ellas no se crea ningún superusuario — usa manage.py createsuperuser
        return
    User = apps.get_model("users", "CustomUser")
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
