from rest_framework import serializers

from backend.settings import NUMBER_OF_IMAGE_PER_PRODUCT
from seller.models import BusinessCustomers
from seller.models import BusinessDetail
from seller.models import Collection
from seller.models import Group
from seller.models import Notifications
from seller.models import ProductImage
from seller.models import Products
from seller.models import Promotion
from seller.models import Staff
from seller.models import User


class LoginSerializers(serializers.ModelSerializer):

    fcm_token = serializers.CharField(write_only=True)
    device_id = serializers.CharField(write_only=True)
    device_type = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "phone_number",
            "id",
            "user_type",
            "fcm_token",
            "device_id",
            "device_type",
        ]
        read_only_fields = ("verification_code", "otp_created_at")

    def create(self, validated_data):
        fcm_token = validated_data.pop("fcm_token")
        device_id = validated_data.pop("device_id")
        device_type = validated_data.pop("device_type")

        return super(LoginSerializers, self).create(validated_data)


class VerifyOTPSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "phone_number",
            "verification_code",
        ]
        read_only_fields = ("is_detail", "otp_created_at")


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = (
            "verification_code",
            "password",
            "last_login",
            "is_superuser",
            "is_active",
            "date_joined",
            "otp_created_at",
            "groups",
            "user_permissions",
        )


class BusinessDetailSerializers(serializers.ModelSerializer):
    class Meta:
        model = BusinessDetail
        fields = "__all__"

    def validate_email(self, attrs):
        if attrs:
            instance = self.context.get("instance")

            business_detail = self.Meta.model.objects.filter(email__iexact=attrs)

            if instance:
                business_detail = business_detail.exclude(id=instance.id)

            if business_detail.exists():
                raise serializers.ValidationError(
                    "This email address is already registered"
                )

        return attrs


class GroupDetailsSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "business_name",
            "first_name",
            "phone_number",
            "city",
            "image",
            "address",
        ]


class GroupDataSerializers(serializers.ModelSerializer):
    customer_detail = serializers.SerializerMethodField()

    class Meta:
        model = Group
        exclude = ["updated_by", "business"]

    def create(self, validated_data):
        business_id = self.context["business_id"]
        updated_by_id = self.context["updated_by_id"]
        validated_data.update(
            {"business_id": business_id, "updated_by_id": updated_by_id}
        )
        group = super(GroupDataSerializers, self).create(validated_data)
        return group

    def get_customer_detail(self, obj):
        grp_data = getattr(obj, "customer")
        return GroupDetailsSerializers(
            grp_data, many=True, read_only=True, context=self.context
        ).data


class StaffSerializers(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = "__all__"


class ProductImageSerializers(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["image"]


class ProductSerializers(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = Products
        fields = "__all__"

    def create(self, validated_data):
        updated_by = validated_data.get("updated_by")
        business = validated_data.get("business")
        images = self.context["images"]
        if len(images) > NUMBER_OF_IMAGE_PER_PRODUCT:
            raise serializers.ValidationError("A product can have a maximum 6 images.")
        product = Products.objects.create(**validated_data)
        for image in images:
            ProductImage.objects.create(
                product=product, business=business, image=image, updated_by=updated_by
            )
        return product

    def update(self, instance, validated_data):
        instance.updated_by = self.context.get("request").user
        instance.price = validated_data.get("price")
        instance.description = validated_data.get("description")
        instance.lmitate = validated_data.get("lmitate")
        instance.unit = validated_data.get("unit")
        instance.name = validated_data.get("name")
        instance.status = validated_data.get("status")

        images = self.context["images"]
        if len(images) > NUMBER_OF_IMAGE_PER_PRODUCT:
            raise serializers.ValidationError("A product can have a maximum 6 images.")
        instance.save()
        if images:
            ProductImage.objects.filter(
                product=instance, business=instance.business
            ).delete()
        for image in images:
            if image:
                ProductImage.objects.create(
                    product=instance,
                    business=instance.business,
                    image=image,
                    updated_by=instance.updated_by,
                )
        return instance

    def get_images(self, obj):
        grp_data = ProductImage.objects.filter(product=obj)
        return ProductImageSerializers(
            grp_data, many=True, read_only=True, context=self.context
        ).data


class PromotionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["name"]


class PromotionProductSerializers(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = Products
        fields = [
            "id",
            "name",
            "price",
            "images",
            "lmitate",
            "description",
            "created_at",
            "status",
            "unit",
        ]

    def get_images(self, obj):
        grp_data = ProductImage.objects.filter(product=obj)
        return ProductImageSerializers(
            grp_data, many=True, read_only=True, context=self.context
        ).data


class PromotionSerializers(serializers.ModelSerializer):
    group = PromotionGroupSerializer(read_only=True, many=True)
    product = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Promotion
        fields = "__all__"

    def get_product(self, obj):
        return PromotionProductSerializers(
            obj.product.exclude(status=Products.DISCONTINUED),
            many=True,
            context=self.context,
        ).data


class CreatePromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = "__all__"

    def create(self, validated_data):
        data = super(CreatePromotionSerializer, self).create(validated_data)
        return data


class RequestUserSerializers(serializers.Serializer):
    customer = serializers.CharField(
        required=True, help_text="Comma separated customer id."
    )

    class Meta:
        model = BusinessCustomers
        fields = ("customer",)


class RequestUserResponseSerializers(serializers.ModelSerializer):
    customer_detail = serializers.SerializerMethodField()

    class Meta:
        model = BusinessCustomers
        fields = "__all__"

    def get_customer_detail(self, obj):
        grp_data = User.objects.filter(id=obj.customer.id)
        return GroupDetailsSerializers(
            grp_data, many=True, read_only=True, context=self.context
        ).data


class NotificationSerializers(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = ("id", "status", "notification_type")


class CollectionDetailsSerializers(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = ["id", "name", "created_at", "products"]

    def get_products(self, obj):
        search = self.context.get("search")
        products = obj.products.all()
        if search:
            products = products.filter(name__icontains=search)
        products = reversed(products)
        return PromotionProductSerializers(
            products, many=True, context=self.context
        ).data


class CollectionSerializers(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = "__all__"

    def to_representation(self, instance):
        serializer = CollectionDetailsSerializers(instance, context=self.context)
        return serializer.data


class EditCollectionProduct(serializers.Serializer):
    product_id = serializers.ListField(
        child=serializers.IntegerField(min_value=0), required=True, write_only=True
    )
    action = serializers.ChoiceField(
        required=True, choices=(("ADD", "add"), ("REMOVE", "remove"))
    )


class SellerCreateCoustomerserializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name",
            "business_name",
            "phone_number",
            "city",
            "address",
            "email",
        ]

        extra_kwargs = {"email": {"required": False}}

    def validate_email(self, attrs):
        if attrs:

            users = self.Meta.model.objects.filter(email__iexact=attrs)

            if users.exists():
                raise serializers.ValidationError(
                    "This email address is already registered"
                )

        return attrs
