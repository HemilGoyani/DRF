# Generated by Django 4.1.1 on 2023-03-14 04:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("seller", "0022_alter_businessdetail_image_alter_productimage_image_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="businessdetail",
            name="payment_message",
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]
