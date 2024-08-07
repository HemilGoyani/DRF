from django.contrib import admin
from django.contrib.auth.models import Group
from django.db import models
from django.forms import Textarea
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter

from seller.models import BusinessDetail
from seller.models import MyFCMDevice
from seller.models import Products
from seller.models import Staff


class Seller(BusinessDetail):
    class Meta:
        proxy = True
        verbose_name = "Business"
        verbose_name_plural = "Business"


class ProductInlineAdmin(admin.TabularInline):
    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 10, "cols": 50})},
    }
    model = Products
    exclude = ("updated_by",)
    extra = 0


class StaffInlineAdmin(admin.TabularInline):
    model = Staff
    exclude = ("updated_by",)
    extra = 0


class SellerAdmin(admin.ModelAdmin):
    list_display = ("business_name", "phone_number", "is_deleted")
    inlines = (StaffInlineAdmin, ProductInlineAdmin)
    fields = (
        "business_name",
        "owner_name",
        "email",
        "phone_number",
        "city",
        "image",
        "is_deleted",
    )
    search_fields = ("phone_number", "business_name")
    list_per_page = 20

    def save_formset(self, request, form, formset, change):
        for inline_form in formset.forms:
            if inline_form.has_changed():
                inline_form.instance.updated_by = request.user
        super().save_formset(request, form, formset, change)


class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "business")
    list_filter = (("business", RelatedDropdownFilter),)
    exclude = ("updated_by",)
    list_per_page = 30


class MyFCMDeviceAdmin(admin.ModelAdmin):
    list_display = ("device_id", "type", "user", "user_type")


# admin.site.register(MyFCMDevice, MyFCMDeviceAdmin)
admin.site.register(Seller, SellerAdmin)
admin.site.register(Products, ProductAdmin)
admin.site.unregister(Group)


admin.site.site_header = "backend Admin"
admin.site.site_title = "backend Admin"
admin.site.index_title = "backend Admin"
