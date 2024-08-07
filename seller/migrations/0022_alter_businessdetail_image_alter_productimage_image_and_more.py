# Generated by Django 4.1.1 on 2023-03-02 06:53

import backend.utils
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("seller", "0021_products_unit"),
    ]

    operations = [
        migrations.AlterField(
            model_name="businessdetail",
            name="image",
            field=models.ImageField(
                blank=True,
                upload_to=backend.utils.get_business_upload_path,
                validators=[backend.utils.validate_file_size],
            ),
        ),
        migrations.AlterField(
            model_name="productimage",
            name="image",
            field=models.ImageField(
                blank=True,
                upload_to=backend.utils.get_product_upload_path,
                validators=[backend.utils.validate_file_size],
            ),
        ),
        migrations.AlterField(
            model_name="staff",
            name="image",
            field=models.ImageField(
                blank=True,
                upload_to=backend.utils.get_staff_upload_path,
                validators=[backend.utils.validate_file_size],
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=backend.utils.get_profile_upload_path,
                validators=[backend.utils.validate_file_size],
            ),
        ),
    ]
