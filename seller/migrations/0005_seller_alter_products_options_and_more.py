# Generated by Django 4.1.1 on 2022-10-16 06:09

from django.db import migrations, models
import seller.models


class Migration(migrations.Migration):

    dependencies = [
        ("seller", "0004_alter_user_phone_number"),
    ]

    operations = [
        migrations.CreateModel(
            name="Seller",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("seller.user",),
            managers=[
                ("objects", seller.models.BaseManager()),
            ],
        ),
        migrations.AlterModelOptions(
            name="products",
            options={"verbose_name": "product"},
        ),
        migrations.AlterField(
            model_name="businessdetail",
            name="business_name",
            field=models.CharField(default="test", max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="products",
            name="name",
            field=models.CharField(default="test", max_length=500),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="products",
            name="price",
            field=models.FloatField(default=10),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="staff",
            name="name",
            field=models.CharField(default="test", max_length=100),
            preserve_default=False,
        ),
    ]
