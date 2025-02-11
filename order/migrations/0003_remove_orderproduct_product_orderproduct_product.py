# Generated by Django 4.1.1 on 2022-10-05 06:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seller', '0002_alter_businessdetail_phone_number_and_more'),
        ('order', '0002_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderproduct',
            name='product',
        ),
        migrations.AddField(
            model_name='orderproduct',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='list_of_order_products', to='seller.products'),
        ),
    ]
