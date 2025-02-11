# Generated by Django 4.1.1 on 2023-03-20 04:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("fcm_django", "0009_alter_fcmdevice_user"),
        ("seller", "0023_businessdetail_payment_message"),
    ]

    operations = [
        migrations.CreateModel(
            name="MyFCMDevice",
            fields=[
                (
                    "fcmdevice_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="fcm_django.fcmdevice",
                    ),
                ),
                ("user_type", models.CharField(max_length=20)),
            ],
            options={
                "verbose_name": "My FCM Device",
                "verbose_name_plural": "My FCM Devices",
            },
            bases=("fcm_django.fcmdevice",),
        ),
    ]
