# Generated by Django 4.1.1 on 2022-10-16 07:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("seller", "0005_seller_alter_products_options_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="seller",
            options={"verbose_name": "Business", "verbose_name_plural": "Business"},
        ),
    ]
