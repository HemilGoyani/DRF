# Generated by Django 4.1.1 on 2022-10-16 06:09

from django.db import migrations, models
import django.db.models.deletion
import seller.models


class Migration(migrations.Migration):

    dependencies = [
        ("seller", "0005_seller_alter_products_options_and_more"),
        ("buyer", "0003_rename_total_amount_cart_amount_cart_business"),
    ]

    operations = [
        migrations.CreateModel(
            name="Buyer",
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
        migrations.AlterField(
            model_name="cart",
            name="amount",
            field=models.FloatField(default=10),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="cart",
            name="business",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cart_business",
                to="seller.businessdetail",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="cart",
            name="quantity",
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
