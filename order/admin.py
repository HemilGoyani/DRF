from django.contrib import admin
from django_admin_listfilter_dropdown.filters import ChoiceDropdownFilter
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter

from .models import Order
from .models import OrderProduct


class OrderDetailAdmin(admin.TabularInline):
    model = OrderProduct
    extra = 1
    max_num = 0
    fields = (
        "product",
        "business",
        "quantity",
        "amount",
    )
    list_display_links = ("product", "business")
    readonly_fields = fields


class OrderAdmin(admin.ModelAdmin):
    inlines = (OrderDetailAdmin,)
    list_display = ("customer", "get_seller", "business", "status")
    list_filter = (
        ("customer", RelatedDropdownFilter),
        ("business", RelatedDropdownFilter),
        ("status", ChoiceDropdownFilter),
    )
    # readonly_fields = ("total_amount", "customer", "business", "created_by")
    exclude = ["updated_by", "business"]
    list_per_page = 20

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_seller(self, obj):
        return obj.business.customer

    get_seller.short_description = "Seller"


admin.site.register(Order, OrderAdmin)
