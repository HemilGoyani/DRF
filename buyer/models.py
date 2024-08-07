from django.db import models

from seller.models import BaseModel, BusinessDetail, Products, User


class Cart(BaseModel):
    customer = models.ForeignKey(
        User, related_name="carts", on_delete=models.CASCADE
    )
    business = models.ForeignKey(
        BusinessDetail, related_name="carts", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Products, related_name="carts", on_delete=models.CASCADE
    )
    quantity = models.IntegerField()
    amount = models.FloatField()

    class Meta:
        db_table = "cart"
