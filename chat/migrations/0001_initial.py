# Generated by Django 4.1.7 on 2023-10-25 22:57

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Chat",
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
                ("agent", models.CharField(blank=True, max_length=52, null=True)),
                ("identifier", models.CharField(blank=True, max_length=72, null=True)),
                ("start_time", models.DateTimeField(auto_now_add=True)),
                ("end_time", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("active", "all active chats"),
                            ("resolved", "all resolved chats"),
                        ],
                        default="active",
                        max_length=20,
                        null=True,
                    ),
                ),
                (
                    "channel",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("email", "Email address"),
                            ("chat", "Enif Chat Channel"),
                            ("facebook", "Business facebook channel"),
                            ("telegram", "Business Telegram channel"),
                            ("twitter", "Business Twitter channel"),
                        ],
                        default="chat",
                        max_length=20,
                        null=True,
                    ),
                ),
                ("read", models.BooleanField(default=False)),
                ("is_auto_response", models.BooleanField(default=False)),
                ("sentiment", models.CharField(default="", max_length=52)),
                ("keyword", models.CharField(default="", max_length=256)),
                ("escalated", models.BooleanField(default=False)),
                ("department", models.CharField(default="", max_length=256)),
                (
                    "chat_session",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=200),
                        blank=True,
                        null=True,
                        size=None,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Customer",
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
                ("name", models.CharField(max_length=256)),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
                (
                    "phone_number",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                (
                    "identifier",
                    models.CharField(
                        blank=True, max_length=256, null=True, unique=True
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Message",
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
                    "sender",
                    models.CharField(
                        choices=[
                            ("customer", "a person that initiates the chat"),
                            ("agent", "a person that reponds to the initiated chat"),
                        ],
                        default="customer",
                        max_length=256,
                    ),
                ),
                ("sanusi_response", models.TextField(blank=True, null=True)),
                ("content", models.TextField()),
                ("sent_time", models.DateTimeField(auto_now_add=True)),
                ("is_multimedia", models.BooleanField(default=False)),
                ("multimedia_url", models.URLField(blank=True, null=True)),
                (
                    "chat",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="chat.chat",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="chat",
            name="customer",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="customer_chats",
                to="chat.customer",
            ),
        ),
    ]
