# Generated by Django 4.1.7 on 2023-05-19 09:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("business", "0004_knowledgebase_knowledgebase_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="knowledgebase",
            name="knowledgebase_id",
            field=models.CharField(blank=True, max_length=72, null=True, unique=True),
        ),
    ]
