# Generated by Django 4.1.7 on 2023-05-02 13:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0003_widgetbehavior_chat_identifier_widgetsettings"),
        ("jarvis", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="chat",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="jarvis_messages",
                to="chat.chat",
            ),
        ),
    ]
