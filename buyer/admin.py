from django.contrib import admin

from order.models import Order
from seller.models import User


class Buyer(User):
    class Meta:
        proxy = True


class OrderDetailAdmin(admin.TabularInline):
    model = Order
    extra = 0
    max_num = 0
    fk_name = "customer"
    fields = ("created_by", "business", "total_amount", "status")
    list_display_links = ("product", "business")
    readonly_fields = fields


class BuyerAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "first_name", "email", "is_deleted")
    fields = (
        "phone_number",
        "business_name",
        "first_name",
        "city",
        "address",
        "is_deleted",
    )
    inlines = (OrderDetailAdmin,)
    list_per_page = 20

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(user_type__contains="BUYER")


admin.site.register(Buyer, BuyerAdmin)
