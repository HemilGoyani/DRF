from rest_framework import serializers

from seller.models import BusinessDetail
from seller.models import ProductImage
from seller.serializers import BusinessDetailSerializers
from seller.serializers import ProductImageSerializers

from .models import Order
from .models import OrderDetail
from .models import OrderProduct
from .models import Products
from .models import User


class OrderProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Products
        fields = "__all__"

    def get_image(self, obj):
        grp_data = ProductImage.objects.filter(product_id=obj)
        return ProductImageSerializers(
            grp_data, many=True, read_only=True, context=self.context
        ).data


class OrderProductDataSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="product.name", read_only=True)
    price = serializers.FloatField(source="product.price", read_only=True)
    description = serializers.CharField(source="product.description", read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = OrderProduct
        fields = [
            "id",
            "name",
            "price",
            "description",
            "image",
            "quantity",
            "lmitate",
        ]

    def get_image(self, obj):
        grp_data = ProductImage.objects.filter(product_id=obj.product)
        return ProductImageSerializers(
            grp_data, many=True, read_only=True, context=self.context
        ).data


class OrderCustomerSerializer(serializers.ModelSerializer):
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
        ]


class OrderSerializers(serializers.ModelSerializer):
    product_details = serializers.SerializerMethodField()
    customer_detail = serializers.SerializerMethodField()
    business_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = "__all__"

    def update(self, instance, validated_data):
        updated_by = validated_data.get("updated_by")
        instance = super(OrderSerializers, self).update(instance, validated_data)
        OrderDetail.objects.create(
            order=instance, status=instance.status, updated_by=updated_by
        )
        return instance

    def get_product_details(self, obj):
        order_product_data = OrderProduct.objects.filter(order=obj)
        return OrderProductDataSerializer(
            order_product_data, many=True, read_only=True, context=self.context
        ).data

    def get_customer_detail(self, obj):
        customer_data = getattr(obj, "customer")
        return OrderCustomerSerializer(
            customer_data, read_only=True, context=self.context
        ).data

    def get_business_name(self, obj):
        business = BusinessDetail.objects.get(id=obj.business.id)
        return business.business_name


class TrackOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetail
        fields = ["order", "created_at", "updated_at", "status", "updated_by"]


class CreateOrderSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        many = kwargs.pop("many", True)
        super(CreateOrderSerializer, self).__init__(many=many, *args, **kwargs)

    class Meta:
        model = OrderProduct
        fields = (
            "product",
            "quantity",
        )
