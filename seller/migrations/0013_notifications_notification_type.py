# Generated by Django 4.1.1 on 2022-12-23 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("seller", "0012_alter_user_user_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="notifications",
            name="notification_type",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
