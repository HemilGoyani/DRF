from django.db import models

from seller.models import BaseModel
from seller.models import BusinessDetail
from seller.models import Products
from seller.models import User

# Create your models here.

ORDER_STATUS = [
    ("Placed", "Placed"),
    ("Processing", "Processing"),
    ("Shipped", "Shipped"),
    ("Cancel", "Cancel"),
]


class Order(BaseModel):
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="orders",
    )
    customer = models.ForeignKey(
        User, related_name="buyer_orders", on_delete=models.CASCADE
    )
    business = models.ForeignKey(
        BusinessDetail, related_name="orders", on_delete=models.CASCADE
    )
    total_amount = models.FloatField()
    status = models.CharField(max_length=20, choices=ORDER_STATUS)
    note = models.CharField(max_length=1000, null=True, blank=True)

    class Meta:
        db_table = "order"

    def __str__(self):
        return "Order"


class OrderDetail(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=ORDER_STATUS)

    class Meta:
        db_table = "order_detail"


class OrderProduct(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(
        Products, related_name="order_products", on_delete=models.CASCADE
    )
    business = models.ForeignKey(
        BusinessDetail, related_name="order_business", on_delete=models.CASCADE
    )
    quantity = models.IntegerField()
    amount = models.FloatField()
    lmitate = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "order_product"
