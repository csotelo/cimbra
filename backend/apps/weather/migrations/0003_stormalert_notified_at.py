from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("weather", "0002_modelartifact"),
    ]

    operations = [
        migrations.AddField(
            model_name="stormalert",
            name="notified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
