# Generated by Django 4.1.1 on 2023-02-03 10:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("seller", "0018_promotion_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="business_name",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
