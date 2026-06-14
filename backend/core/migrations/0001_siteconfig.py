from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SiteConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("site_name", models.CharField(default="Ximbra", max_length=100)),
                ("site_description", models.TextField(blank=True, default="")),
                ("og_image_url", models.URLField(blank=True, default="",
                                                  help_text="URL de imagen para Open Graph (redes sociales)")),
                ("favicon_url", models.URLField(blank=True, default="",
                                                help_text="URL del favicon (.ico o .png)")),
                ("allow_indexing", models.BooleanField(default=False,
                                                       help_text="Permitir indexación por buscadores (robots.txt)")),
                ("primary_color", models.CharField(default="#4f46e5", max_length=7,
                                                   help_text="Color primario hex (#rrggbb) — skin del sistema")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "site_config"},
        ),
    ]
