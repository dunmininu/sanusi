# Generated by Django 4.1.7 on 2023-10-25 22:57

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Lead",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(blank=True, default="", max_length=256),
                ),
                ("last_name", models.CharField(blank=True, default="", max_length=256)),
                (
                    "phone_number",
                    models.CharField(blank=True, default="", max_length=256),
                ),
                ("email", models.EmailField(blank=True, max_length=256, null=True)),
            ],
        ),
    ]
