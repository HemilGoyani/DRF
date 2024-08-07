from django.db import models
from seller.models import User
from seller.models import BusinessDetail
from seller.models import Staff
from seller.models import ProductImage

from django.dispatch import receiver


@receiver(models.signals.post_delete, sender=User)
def remove_image_from_user(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)


@receiver(models.signals.post_delete, sender=BusinessDetail)
def remove_image_from_business_detail(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)


@receiver(models.signals.post_delete, sender=Staff)
def remove_image_from_staff(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)


@receiver(models.signals.post_delete, sender=ProductImage)
def remove_image_from_product_image(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
