from datetime import datetime
from datetime import timedelta

from rest_framework import serializers

from seller.models import BusinessCustomers
from seller.models import BusinessDetail
from seller.models import Collection
from seller.models import Group
from seller.models import Notifications
from seller.models import Products
from seller.models import Promotion
from seller.models import User
from seller.serializers import BusinessDetailSerializers
from seller.serializers import ProductSerializers
from seller.serializers import PromotionProductSerializers


class CreateCustomerSerializers(serializers.ModelSerializer):
    customer_invite_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "business_name",
            "first_name",
            "phone_number",
            "city",
            "address",
            "image",
            "is_detail",
            "customer_invite_status",
            "email",
            "is_deleted",
        ]
        read_only_fields = ("id",)

    def validate_email(self, attrs):
        if attrs:
            instance = self.context.get("instance")

            users = self.Meta.model.objects.filter(email__iexact=attrs)

            if instance:
                users = users.exclude(id=instance.id)

            if users.exists():
                raise serializers.ValidationError(
                    "This email address is already registered"
                )

        return attrs

    def get_customer_invite_status(self, obj):
        user = self.context["request"].user
        if user.business_details.first():
            business = user.business_details.first()
        elif user.staff_business_details.first():
            business = user.staff_business_details.first()
        else:
            return None

        invite_obj = obj.business_customers.filter(business_id=business.id).first()
        if invite_obj:
            return invite_obj.status
        return None


class BusinessProductsSerializers(serializers.ModelSerializer):
    products_details = serializers.SerializerMethodField()

    class Meta:
        model = BusinessDetail
        fields = "__all__"

    def get_products_details(self, obj):
        grp_data = Products.objects.filter(business=obj).exclude(
            status=Products.DISCONTINUED
        )
        search = self.context.get("search")
        if search:
            grp_data = grp_data.filter(name__icontains=search)
        return ProductSerializers(
            grp_data, many=True, read_only=True, context=self.context
        ).data


class Dealserializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()

    class Meta:
        model = Promotion
        exclude = ("customer", "group", "business", "product")

    def get_products(self, obj):
        return PromotionProductSerializers(
            obj.product.exclude(status=Products.DISCONTINUED),
            many=True,
            read_only=True,
            context=self.context,
        ).data


class BusinessSerializer(serializers.ModelSerializer):
    deals = serializers.SerializerMethodField()

    class Meta:
        model = BusinessDetail
        fields = "__all__"

    def get_deals(self, obj):
        promotions = obj.promotions.filter(
            created_at__gte=datetime.now() - timedelta(days=7),
            group__customer__in=[self.context["request"].user],
        )
        return Dealserializer(
            promotions, many=True, read_only=True, context=self.context
        ).data


class NotificationDetailSerializers(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        exclude = ["updated_by", "sender", "receiver"]


class DirectAddCustomerSerializers(serializers.ModelSerializer):
    class Meta:
        model = BusinessCustomers
        fields = "__all__"


class BusinessCollectionSerializers(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = "__all__"
