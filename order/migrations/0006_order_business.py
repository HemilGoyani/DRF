# Generated by Django 4.1.1 on 2022-10-10 05:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seller', '0002_alter_businessdetail_phone_number_and_more'),
        ('order', '0005_order_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='business',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders_business', to='seller.businessdetail'),
        ),
    ]
