import os
import random
import uuid
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError


def create_four_digit_verification_code(phone):
    if phone:
        """Generate a random 4-digit OTP"""
        return random.randint(1000, 9999)
    else:
        return False


def validate_file_size(value):
    filesize = value.size
    if filesize >= 1024 * 1024 * settings.MAX_FILE_SIZE:
        raise ValidationError(
            f"Image file size should be less than {settings.MAX_FILE_SIZE}MB"
        )


def get_profile_upload_path(instance, filename):
    now = datetime.now()
    unique_id = uuid.uuid4().hex
    basename, extension = os.path.splitext(filename)
    return os.path.join(
        f"{instance.user_type}".lower(),
        f"{instance.first_name}".lower(),
        "profile",
        "{date}-{unique_id}{extension}".format(
            date=now.strftime("%Y-%m-%d_%H-%M-%S"),
            unique_id=unique_id,
            extension=extension,
        ),
    )


def get_business_upload_path(instance, filename):
    now = datetime.now()
    unique_id = uuid.uuid4().hex
    basename, extension = os.path.splitext(filename)
    return os.path.join(
        "seller",
        f"{instance.business_name}".lower(),
        "business_images",
        "{date}-{unique_id}{extension}".format(
            date=now.strftime("%Y-%m-%d_%H-%M-%S"),
            unique_id=unique_id,
            extension=extension,
        ),
    )


def get_product_upload_path(instance, filename):
    now = datetime.now()
    unique_id = uuid.uuid4().hex
    basename, extension = os.path.splitext(filename)
    return os.path.join(
        "seller",
        f"{instance.business.business_name}".lower(),
        "product_images",
        "{date}-{unique_id}{extension}".format(
            date=now.strftime("%Y-%m-%d_%H-%M-%S"),
            unique_id=unique_id,
            extension=extension,
        ),
    )


def get_staff_upload_path(instance, filename):
    now = datetime.now()
    unique_id = uuid.uuid4().hex
    basename, extension = os.path.splitext(filename)
    return os.path.join(
        "seller",
        f"{instance.business.business_name}".lower(),
        "staff_profile_images",
        "{date}-{unique_id}{extension}".format(
            date=now.strftime("%Y-%m-%d_%H-%M-%S"),
            unique_id=unique_id,
            extension=extension,
        ),
    )
