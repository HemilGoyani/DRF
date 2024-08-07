from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from fcm_django.models import FCMDevice
from multiselectfield import MultiSelectField
from phonenumber_field.modelfields import PhoneNumberField

from backend.settings import OTP_TIMEOUT
from backend.utils import get_business_upload_path
from backend.utils import get_product_upload_path
from backend.utils import get_profile_upload_path
from backend.utils import get_staff_upload_path
from backend.utils import validate_file_size


class MyFCMDevice(FCMDevice):
    user_type = models.CharField(max_length=20)

    class Meta:
        verbose_name = "My FCM Device"
        verbose_name_plural = "My FCM Devices"


USER_TYPE = [("SELLER", "SELLER"), ("BUYER", "BUYER")]


class BaseManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, phone_number, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), blank=True)
    user_type = MultiSelectField(max_length=255, choices=USER_TYPE)
    phone_number = PhoneNumberField(
        verbose_name="Phone no.",
        help_text="Provide a number with country code (e.g. +12125552368).",
        unique=True,
    )
    verification_code = models.CharField(max_length=10, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    image = models.ImageField(
        upload_to=get_profile_upload_path,
        null=True,
        blank=True,
        validators=[validate_file_size],
    )
    is_detail = models.BooleanField(default=False)
    is_business_staff = models.BooleanField(default=False)
    business_name = models.CharField(max_length=200, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    objects = BaseManager()

    def __str__(self):
        if self.business_name:
            return str(f"{self.business_name} {self.phone_number}")
        elif self.first_name:
            return str(f"{self.first_name} {self.phone_number}")
        else:
            return str(self.phone_number)

    def verify_otp(self, otp):
        return (
            otp == self.verification_code
            and self.otp_created_at + timedelta(minutes=OTP_TIMEOUT) > timezone.now()
        )

    class Meta:
        unique_together = ("email", "phone_number")
        db_table = "user"


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        abstract = True


class BusinessDetail(BaseModel):
    customer = models.ForeignKey(
        User, related_name="business_details", on_delete=models.CASCADE
    )
    business_name = models.CharField(max_length=100)
    owner_name = models.CharField(max_length=200)
    email = models.EmailField(_("email_address"), blank=True)
    phone_number = PhoneNumberField(
        null=True,
        blank=True,
        verbose_name="Phone no.",
        help_text="Provide a number with country code (e.g. +12125552368).",
    )
    city = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(
        upload_to=get_business_upload_path,
        blank=True,
        validators=[validate_file_size],
    )
    is_detail = models.BooleanField(default=False)
    staff = models.ManyToManyField(
        User, related_name="staff_business_details", blank=True
    )
    payment_message = models.CharField(max_length=1000, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.business_name

    class Meta:
        db_table = "business_detail"


class Group(BaseModel):
    name = models.CharField(max_length=200)
    customer = models.ManyToManyField(User, related_name="group_customers")
    business = models.ForeignKey(
        BusinessDetail, related_name="groups", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "group"


class Staff(BaseModel):
    business = models.ForeignKey(
        BusinessDetail, related_name="staff_business", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    phone_number = PhoneNumberField(
        null=True,
        blank=True,
        verbose_name="Phone no.",
        help_text="Provide a number with country code (e.g. +12125552368).",
    )
    position = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(
        upload_to=get_staff_upload_path,
        blank=True,
        validators=[validate_file_size],
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "staff"


class Products(BaseModel):
    ACTIVE = 1
    OUT_OF_STOCK = 2
    DISCONTINUED = 3

    STATUSES = [
        (ACTIVE, "Active"),
        (OUT_OF_STOCK, "Out of stock"),
        (DISCONTINUED, "Discontinued"),
    ]

    business = models.ForeignKey(
        BusinessDetail, related_name="products", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=500)
    price = models.FloatField()
    unit = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    lmitate = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUSES,
        default=ACTIVE,
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "product"
        verbose_name = "product"


class ProductImage(BaseModel):
    product = models.ForeignKey(
        Products, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(
        upload_to=get_product_upload_path,
        blank=True,
        validators=[validate_file_size],
    )
    business = models.ForeignKey(BusinessDetail, on_delete=models.CASCADE)

    class Meta:
        db_table = "product_image"


class Collection(BaseModel):
    name = models.CharField(max_length=500)
    business = models.ForeignKey(
        BusinessDetail, related_name="collections", on_delete=models.CASCADE
    )
    products = models.ManyToManyField(Products, related_name="collections")


class Promotion(BaseModel):
    name = models.CharField(max_length=255, blank=True, null=True)
    business = models.ForeignKey(
        BusinessDetail, related_name="promotions", on_delete=models.CASCADE
    )
    customer = models.ForeignKey(
        User, related_name="promotions", on_delete=models.CASCADE
    )
    product = models.ManyToManyField(Products, related_name="promotions")
    group = models.ManyToManyField(Group, related_name="promotions")

    class Meta:
        db_table = "promotion"


class Notifications(BaseModel):
    sender = models.ForeignKey(
        User, related_name="sender_notifications", on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        User, related_name="receiver_notifications", on_delete=models.CASCADE
    )
    message = models.TextField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    notification_type = models.CharField(max_length=50, null=True, blank=True)
    order = models.ForeignKey(
        "order.Order", related_name="notifications", on_delete=models.CASCADE, null=True
    )

    class Meta:
        db_table = "notification"


class BusinessCustomers(BaseModel):
    STATUS = (
        ("Pending", "PENDING"),
        ("Accept", "ACCEPT"),
        ("Reject", "REJECT"),
    )
    business = models.ForeignKey(
        BusinessDetail, related_name="business_customers", on_delete=models.CASCADE
    )
    customer = models.ForeignKey(
        User, related_name="business_customers", on_delete=models.CASCADE
    )
    status = models.CharField(max_length=20, choices=STATUS)
    notification = models.ForeignKey(
        Notifications,
        related_name="business_customers",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "business_customer"
