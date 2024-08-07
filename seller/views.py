import calendar
from datetime import date
from datetime import datetime
from datetime import timedelta

import plivo
from django.conf import settings
from django.db.models import Count
from django.db.models import F
from django.db.models import Q
from django.template.loader import get_template
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.generics import ListAPIView
from rest_framework.generics import ListCreateAPIView
from rest_framework.generics import RetrieveDestroyAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from buyer.serializers import CreateCustomerSerializers
from buyer.serializers import NotificationDetailSerializers
from backend.utils import create_four_digit_verification_code
from seller.utils import PaginationClass
from seller.utils import push_notification

from .models import BusinessCustomers
from .models import BusinessDetail
from .models import Collection
from .models import Group
from .models import Notifications
from .models import Products
from .models import Promotion
from .models import Staff
from .models import User
from .serializers import BusinessDetailSerializers
from .serializers import CollectionDetailsSerializers
from .serializers import CollectionSerializers
from .serializers import CreatePromotionSerializer
from .serializers import EditCollectionProduct
from .serializers import GroupDataSerializers
from .serializers import LoginSerializers
from .serializers import ProductSerializers
from .serializers import PromotionSerializers
from .serializers import RequestUserResponseSerializers
from .serializers import RequestUserSerializers
from .serializers import SellerCreateCoustomerserializer
from .serializers import StaffSerializers
from .serializers import UserProfileSerializer
from .serializers import VerifyOTPSerializers
from .utils import fcm_update


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def get_updated_user_type(db_user_type, new_user_type):
    if new_user_type in db_user_type:
        return db_user_type
    else:
        db_user_type.append(new_user_type)
        user_type = ",".join(db_user_type)
        return [user_type]


def send_otp(phone_number, key):
    POWERPACK_UUID = settings.POWERPACK_UUID
    client = plivo.RestClient(
        auth_id=settings.PLIVO_ACCOUNT_ID,
        auth_token=settings.PLIVO_AUTH_TOKEN,
    )
    client.messages.create(
        dst=f"{phone_number}",
        text=f"backend verification code is: {key}",
        powerpack_uuid=POWERPACK_UUID,
    )


def check_and_update_account_status(user, status):

    if status == "SELLER":
        business_detail = BusinessDetail.objects.filter(customer=user.id).first()
        if business_detail and business_detail.is_deleted:
            return False
            # business_detail.is_deleted = False
            # business_detail.save()
    elif user.is_deleted:
        return False
        # user.is_deleted = False
        # user.save()
    return True


class SendOTP(GenericAPIView):
    queryset = User.objects.all()
    serializer_class = LoginSerializers
    permission_classes = [
        AllowAny,
    ]

    def post(self, request, *args, **kwargs):
        phone_number = request.data.get("phone_number")
        if phone_number:
            user_type = request.data.get("user_type", None)
            if not user_type:
                return Response(
                    {"detail": "Please Provide user type."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            phone = str(phone_number)
            key = create_four_digit_verification_code(phone_number)
            if key:
                user = User.objects.filter(phone_number__iexact=phone).first()
                if user:
                    check_status = check_and_update_account_status(user, user_type)
                    if not check_status:
                        return Response(
                            {
                                "detail": "Your account is deleted, please contact our support team for further assistance."
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    user.verification_code = key
                    user.otp_created_at = timezone.now()
                    user.user_type = get_updated_user_type(user.user_type, user_type)
                    user.save()
                    fcm_update(
                        request.data.get("fcm_token"),
                        request.data.get("device_id"),
                        request.data.get("device_type"),
                        user,
                        user_type,
                    )
                    send_otp(phone_number, key)
                    return Response(
                        {"detail": "Otp sent successfully."},
                        status=status.HTTP_202_ACCEPTED,
                    )
                else:
                    serializer = self.serializer_class(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    fcm_token = request.data.get("fcm_token")
                    device_id = request.data.get("device_id")
                    device_type = request.data.get("device_type")
                    user_instance = serializer.save(
                        verification_code=key,
                        otp_created_at=timezone.now(),
                        user_type=user_type,
                    )
                    fcm_update(
                        fcm_token, device_id, device_type, user_instance, user_type
                    )
                    send_otp(phone_number, key)
                    return Response(
                        {"detail": "Otp sent successfully."},
                        status=status.HTTP_201_CREATED,
                    )
            else:
                return Response(
                    {"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(
                {"detail": "Please Enter phone number."},
                status=status.HTTP_404_NOT_FOUND,
            )


class VerifyOTP(GenericAPIView):
    parser_classes = (MultiPartParser,)
    permission_classes = [
        AllowAny,
    ]
    serializer_class = VerifyOTPSerializers

    def post(self, request):
        phone = request.data.get("phone_number", None)
        verification_code = request.data.get("verification_code", None)
        user_type = request.data.get("user_type", None)

        if not user_type or user_type not in ["SELLER", "BUYER"]:
            return Response(
                {
                    "detail": "Value user_type is missing or invalid; value should be 'SELLER or BUYER'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if verification_code and phone:
            user = User.objects.filter(phone_number__iexact=phone).first()
            if user:
                if user.verify_otp(verification_code):
                    user.verification_code = None
                    user.save()
                    is_business = bool(
                        BusinessDetail.objects.filter(is_deleted=False).filter(
                            Q(customer=user.id) | Q(staff=user.id)
                        )
                    )
                    if user.is_business_staff:
                        today = date.today()
                        business = (
                            BusinessDetail.objects.filter(
                                is_deleted=False, staff=user.id
                            )
                            .first()
                            .customer.id
                        )
                        month = calendar.month_name[today.month]
                        notification_data = {}
                        notification_data["sender_id"] = user.id
                        notification_data["title"] = "New Notification From backend"
                        notification_data[
                            "body"
                        ] = f"On {today.day} {month} {today.year} your staff member {user.first_name} logged in your business Profile"
                        notification_data["receiver_id"] = business
                        push_notification(
                            notification_data=notification_data,
                            user=business,
                            send_to="SELLER",
                        )
                        Notifications.objects.create(
                            sender_id=notification_data["sender_id"],
                            receiver_id=notification_data["receiver_id"],
                            message=notification_data["body"],
                            notification_type="staff_login",
                            updated_by_id=request.user.id,
                        )
                    return Response(
                        {
                            "detail": get_tokens_for_user(user),
                            "user": UserProfileSerializer(user).data,
                            "is_detail": user.is_detail
                            if "BUYER" == user_type
                            else is_business,
                        },
                        status=status.HTTP_202_ACCEPTED,
                    )
                else:
                    return Response(
                        {"detail": "Incorrect OTP."}, status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {"detail": f"User not found with phone number: {phone}"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            return Response(
                {"detail": "Phone number or verification code is missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class BusinessCreate(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BusinessDetailSerializers

    def post(self, request, *args, **kwargs):
        data = request.data
        if data:
            data._mutable = True
        data.update(
            {
                "customer": request.user.id,
                "updated_by": request.user.id,
                "is_detail": True,
            }
        )
        serializer = self.serializer_class(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        data = (
            BusinessDetail.objects.filter(is_deleted=False)
            .filter(Q(customer=request.user.id) | Q(staff=request.user.id))
            .first()
        )
        if not data:
            return Response(
                {"detail": "Business Not Found"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.serializer_class(data, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class BusinessDetails(GenericAPIView):
    queryset = BusinessDetail.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]
    serializer_class = BusinessDetailSerializers

    def get_queryset(self):
        if not self.request.user.is_anonymous:
            return (
                super()
                .get_queryset()
                .filter(
                    Q(customer=self.request.user.id) | Q(staff=self.request.user.id)
                )
            )

    def get(self, request, business_id, *args, **kwargs):
        data = self.get_queryset().filter(id=business_id).first()
        if data:
            serializer = self.serializer_class(
                instance=data, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, business_id, *args, **kwargs):
        data = self.get_queryset().filter(id=business_id).first()
        if data:
            if (
                request.data.get("is_deleted") == "true"
                and data.customer != request.user
            ):
                return Response(
                    {"detail": "Only bussines owner can delete the account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = self.serializer_class(
                instance=data,
                data=request.data,
                partial=True,
                context={"request": request, "instance": data},
            )
            serializer.is_valid(raise_exception=True)
            obj = serializer.save()
            if request.data.get("remove_image"):
                obj.image = None
                obj.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response({}, status=status.HTTP_404_NOT_FOUND)


class AllCustomerDetails(ListAPIView):
    pagination_class = PaginationClass
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = CreateCustomerSerializers
    filter_backends = [filters.SearchFilter]
    search_fields = ["phone_number", "first_name"]

    def get_queryset(self):
        queryset = User.objects.all()
        if not self.request.user.is_anonymous:
            instance = queryset.filter(
                is_deleted=False, user_type__icontains="BUYER"
            ).order_by("-date_joined")
            return instance


class GroupDetailView(ListCreateAPIView, GenericAPIView):
    parser_classes = (MultiPartParser,)
    queryset = Group.objects.all()
    pagination_class = PaginationClass
    permission_classes = [IsAuthenticated]
    serializer_class = GroupDataSerializers
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        if not self.request.user.is_anonymous:
            return (
                super()
                .get_queryset()
                .filter(
                    Q(business_id__customer=self.request.user.id)
                    | Q(business_id__staff=self.request.user.id)
                )
                .annotate(Count("id"))
                .order_by("-created_at")
            )

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        customer_id = data["customer"].split(",")
        business_detail = (
            BusinessDetail.objects.filter(is_deleted=False)
            .filter(Q(customer=request.user) | Q(staff=request.user))
            .first()
        )
        data = {"name": data["name"], "customer": customer_id}
        serializer = self.serializer_class(
            data=data,
            context={
                "request": request,
                "business_id": business_detail.id,
                "updated_by_id": request.user.id,
                "customer": customer_id,
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class GroupView(GenericAPIView):
    queryset = Group.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = GroupDataSerializers

    def get(self, request, group_id, *args, **kwargs):
        group = self.get_queryset().filter(id=group_id).first()
        if group:
            serializer = self.serializer_class(
                instance=group, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"detail:Record Not Found."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, group_id, *args, **kwargs):
        instance = self.get_queryset().filter(id=group_id).first()
        if instance:
            add_customer = request.data.get("customer", None)
            if add_customer:
                for customer in add_customer.split(","):
                    instance.customer.add(customer)
            remove_customer = request.data.get("remove_customer")
            if remove_customer:
                instance.customer.remove(remove_customer)
            serializer = self.serializer_class(instance)
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(
            {"detail": "Record Not Found."}, status=status.HTTP_404_NOT_FOUND
        )

    def delete(self, request, group_id, *args, **kwargs):
        instance = self.get_queryset().filter(id=group_id).first()
        if instance:
            instance.delete()
            return Response({"detail": "Group deleted successfully."})
        return Response({"detail": f"group not found."})


class StaffDetailsView(ListAPIView, GenericAPIView):
    queryset = Staff.objects.all()
    pagination_class = PaginationClass
    permission_classes = [IsAuthenticated]
    serializer_class = StaffSerializers

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                Q(business_id__customer=self.request.user.id)
                | Q(business_id__staff=self.request.user.id)
            )
            .annotate(Count("id"))
            .order_by("-created_at")
        )

    def post(self, request, *args, **kwargs):
        data = request.data
        business_detail = (
            BusinessDetail.objects.filter(is_deleted=False)
            .filter(Q(customer_id=request.user.id) | Q(staff=request.user.id))
            .first()
        )

        if not business_detail:
            return Response(
                {"detail": f"Business not found!"}, status=status.HTTP_404_NOT_FOUND
            )
        if User.objects.filter(phone_number=data.get("phone_number")).exists():
            return Response(
                {
                    "detail": f"User already exists with phone number {data.get('phone_number')}!"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        user_data = User.objects.create(
            first_name=data.get("name"),
            phone_number=data.get("phone_number"),
            image=data.get("image"),
            user_type="SELLER",
            is_business_staff=True,
            is_detail=True,
        )

        business_detail.staff.add(user_data.id)

        staff = Staff.objects.create(
            business=business_detail,
            name=data.get("name"),
            phone_number=data.get("phone_number"),
            image=data.get("image"),
            position=data.get("position"),
            updated_by=request.user,
        )

        serializer = self.serializer_class(staff, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class StaffDetail(GenericAPIView):
    queryset = Staff.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = StaffSerializers

    def delete(self, request, staff_id, *args, **kwargs):
        instance = self.get_queryset().filter(id=staff_id).first()
        if instance:
            user = User.objects.filter(phone_number=instance.phone_number).first()
            if user:
                user.delete()
            instance.delete()
            return Response(
                {"detail": "Record deleted successfully."},
                status=status.HTTP_202_ACCEPTED,
            )
        return Response(
            {"detail": "Record Not Found."}, status=status.HTTP_404_NOT_FOUND
        )


class ProductsView(ListCreateAPIView, GenericAPIView):
    queryset = Products.objects.all()
    pagination_class = PaginationClass
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializers
    filter_backends = [filters.SearchFilter]
    search_fields = [
        "name",
    ]

    def get_queryset(self):
        if not self.request.user.is_anonymous:
            return (
                super()
                .get_queryset()
                .filter(
                    Q(business_id__customer=self.request.user.id)
                    | Q(business_id__staff=self.request.user.id)
                )
                .annotate(Count("id"))
                .order_by("-created_at")
            )

    def post(self, request, *args, **kwargs):
        data = request.data
        if data:
            data._mutable = True
        images = data.getlist("image")
        business_detail = (
            BusinessDetail.objects.filter(is_deleted=False)
            .filter(Q(customer_id=request.user.id) | Q(staff=request.user.id))
            .first()
        )
        data.update({"updated_by": request.user.id, "business": business_detail.id})
        serializer = self.serializer_class(
            data=data, context={"images": images, "request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductDetailView(GenericAPIView):
    queryset = Products.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializers

    def get(self, request, product_id, *args, **kwargs):
        instance = self.get_queryset().filter(id=product_id)
        instance = instance.filter(
            Q(business_id__customer=self.request.user.id)
            | Q(business_id__staff=self.request.user.id)
        ).first()
        if instance:
            serializer = self.serializer_class(
                instance=instance, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            {"detail": "Record Not Found"}, status=status.HTTP_404_NOT_FOUND
        )

    def patch(self, request, product_id, *args, **kwargs):
        instance = self.get_queryset().filter(id=product_id)
        instance = instance.filter(
            Q(business_id__customer=self.request.user.id)
            | Q(business_id__staff=self.request.user.id)
        ).first()
        if instance:
            images = request.data.getlist("image")
            serializer = self.serializer_class(
                instance=instance,
                data=request.data,
                partial=True,
                context={"images": images, "request": request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(
            {"detail": "Record Not Found."}, status=status.HTTP_404_NOT_FOUND
        )

    def delete(self, request, product_id, *args, **kwargs):
        instance = self.get_queryset().filter(id=product_id)
        instance = instance.filter(
            Q(business_id__customer=self.request.user.id)
            | Q(business_id__staff=self.request.user.id)
        ).first()

        if not instance:
            return Response(
                {"detail": "Product Not Found."}, status=status.HTTP_404_NOT_FOUND
            )

        instance.delete()
        return Response(
            {"detail": "Record deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )


class PromotionView(ListCreateAPIView, GenericAPIView):
    queryset = Promotion.objects.all()
    pagination_class = PaginationClass
    permission_classes = [IsAuthenticated]
    serializer_class = PromotionSerializers

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                created_at__gte=datetime.now() - timedelta(days=7),
                product__isnull=False,
            )
            .filter(
                Q(business_id__customer=self.request.user.id)
                | Q(business_id__staff=self.request.user.id)
            )
            .annotate(Count("id"))
            .order_by("-created_at")
        )

    def post(self, request, *args, **kwargs):
        products = request.data.get("product").split(",")
        groups = request.data.get("group").split(",")
        business_detail = (
            BusinessDetail.objects.filter(is_deleted=False)
            .filter(Q(customer_id=request.user.id) | Q(staff=request.user.id))
            .first()
        )
        data = {
            "updated_by": request.user.id,
            "business": business_detail.id,
            "customer": request.user.id,
            "product": products,
            "group": groups,
            "name": request.data.get("name"),
        }
        serializer = CreatePromotionSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        notification_data = {}
        notification_data["sender_id"] = request.user.id
        notification_data["title"] = "New Notification From backend"
        notification_data[
            "body"
        ] = f"New deals are available {business_detail.business_name}."

        promotion_groups = Group.objects.filter(id__in=groups)
        business_customers = []

        for group in promotion_groups:
            business_customers.extend(group.customer.all())

        notification_to_create = []
        for business_customer in business_customers:
            notification_data["receiver_id"] = business_customer.id
            push_notification(
                notification_data=notification_data, user=business_customer.id
            )
            notification_to_create.append(
                Notifications(
                    sender_id=notification_data["sender_id"],
                    receiver_id=notification_data["receiver_id"],
                    message=notification_data["body"],
                    notification_type="request_customer",
                    updated_by_id=request.user.id,
                )
            )
        Notifications.objects.bulk_create(notification_to_create)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RequestCustomer(ListCreateAPIView, GenericAPIView):
    parser_classes = (MultiPartParser,)
    queryset = BusinessCustomers.objects.all()
    pagination_class = PaginationClass
    permission_classes = [IsAuthenticated]
    serializer_class = RequestUserSerializers

    search = openapi.Parameter(
        "search", openapi.IN_QUERY, description="Search", type=openapi.TYPE_STRING
    )

    @swagger_auto_schema(manual_parameters=[search])
    def get_queryset(self):
        queryset = BusinessCustomers.objects.all()
        if not self.request.user.is_anonymous:
            search = self.request.query_params.get("search")
            if search:
                data = User.objects.filter(
                    Q(first_name__icontains=search) | Q(phone_number__icontains=search)
                ).values_list("id", flat=True)
                queryset = self.queryset.filter(Q(customer__in=data))

            queryset = (
                queryset.filter(
                    Q(status="Accept")
                    & (
                        Q(business_id__customer=self.request.user.id)
                        | Q(business_id__staff=self.request.user.id)
                    )
                )
                .annotate(Count("id"))
                .order_by("-created_at")
            )
            return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return self.serializer_class
        return RequestUserResponseSerializers

    def post(self, request, *args, **kwargs):
        customer_id_list = request.data.get("customer").split(",")
        business_detail = (
            BusinessDetail.objects.filter(is_deleted=False)
            .filter(Q(customer_id=request.user.id) | Q(staff=request.user.id))
            .first()
        )

        if not business_detail:
            return Response(
                {"detail": "Business not found with requested seller."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notification_data = {}
        notification_data["sender_id"] = request.user.id
        notification_data["title"] = "New Notification From backend"
        notification_data[
            "body"
        ] = f"Request from Business {business_detail.business_name}"

        for customer_id in customer_id_list:
            customer = User.objects.filter(is_deleted=False, id=customer_id).first()
            if customer:
                business_customer = BusinessCustomers.objects.create(
                    business=business_detail,
                    customer=customer,
                    status="Pending",
                    updated_by=request.user,
                )

                push_notification(notification_data=notification_data, user=customer_id)
                notification = Notifications.objects.create(
                    sender_id=notification_data["sender_id"],
                    receiver_id=customer_id,
                    message=notification_data["body"],
                    status="Pending",
                    notification_type="request_customer",
                    updated_by_id=request.user.id,
                )
                business_customer.notification = notification
                business_customer.save()
        return Response(
            {"detail": "Request sent successfully."}, status=status.HTTP_201_CREATED
        )


class SellerNotification(ListCreateAPIView, GenericAPIView):
    queryset = Notifications.objects.all()
    pagination_class = PaginationClass
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationDetailSerializers

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                receiver_id=self.request.user.id, receiver__user_type__contains="SELLER"
            )
            .order_by("-created_at")
        )


class CollectionListCreateView(ListCreateAPIView):
    queryset = Collection.objects.all()
    pagination_class = PaginationClass
    permission_classes = [IsAuthenticated]
    serializer_class = CollectionSerializers
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                Q(business_id__customer=self.request.user.id)
                | Q(business_id__staff=self.request.user.id)
            )
            .annotate(Count("id"))
        )

    def post(self, request, *args, **kwargs):
        data = request.data
        business_detail = (
            BusinessDetail.objects.filter(is_deleted=False)
            .filter(Q(customer_id=request.user.id) | Q(staff=request.user.id))
            .first()
        )

        data.update(
            {
                "updated_by": request.user.id,
                "business": business_detail.id,
            }
        )

        serializer = self.serializer_class(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CollectionRetrieveDestroyAPIView(RetrieveDestroyAPIView):
    queryset = Collection.objects.all()
    pagination_class = PaginationClass
    permission_classes = [IsAuthenticated]
    serializer_class = CollectionSerializers
    lookup_url_kwarg = "collection_id"
    parser_classes = (MultiPartParser,)

    search = openapi.Parameter(
        "search",
        openapi.IN_QUERY,
        description="Search product by name.",
        type=openapi.TYPE_STRING,
    )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": "Collection deleted successfully."}, status=status.HTTP_200_OK
        )

    @swagger_auto_schema(manual_parameters=[search])
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def get_serializer_context(self):
        search = self.request.query_params.get("search")
        context = super().get_serializer_context()
        context.update({"request": self.request, "search": search})
        return context


class CollectionEditAPIView(GenericAPIView):
    parser_classes = (MultiPartParser,)
    queryset = Collection.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = EditCollectionProduct

    def patch(self, request, collection_id, *args, **kwargs):
        data = request.data
        try:
            product_id_list = list(set(int(i) for i in data["product_id"].split(",")))
        except:
            return Response(
                {
                    "detail": "Invalid value pass for 'product_id', it should be an integer!"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        collection = (
            Collection.objects.filter(id=collection_id)
            .filter(
                Q(business_id__customer=self.request.user.id)
                | Q(business_id__staff=self.request.user.id)
            )
            .first()
        )

        if not collection:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        collection_product = list(
            collection.products.all().values_list("id", flat=True)
        )

        if data["action"] == "REMOVE":
            if not all(item in collection_product for item in product_id_list):
                return Response(
                    {"detail": "Product not exist in collection!"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            collection.products.remove(*product_id_list)
        else:
            product = Products.objects.filter(
                Q(business_id__customer=self.request.user.id)
                | Q(business_id__staff=self.request.user.id),
                id__in=product_id_list,
            ).all()
            if not product:
                return Response(
                    {"detail": "Product not Found!"}, status=status.HTTP_404_NOT_FOUND
                )
            collection.products.add(*product_id_list)

        return Response(
            CollectionDetailsSerializers(
                collection, context={"request": self.request}
            ).data,
            status=status.HTTP_200_OK,
        )


from phonenumber_field.phonenumber import PhoneNumber
from phonenumber_field.phonenumber import to_python


class CreateCustomer(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SellerCreateCoustomerserializer

    @swagger_auto_schema(request_body=SellerCreateCoustomerserializer())
    def post(self, request, *args, **kwargs):
        seller, data = request.user, request.data.copy()
        data.update({"user_type": "BUYER"})
        phone_number = to_python(data.get("phone_number"))
        if isinstance(phone_number, PhoneNumber) and not phone_number.is_valid():
            return Response(
                {"detail": "The phone number entered is not valid."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        business = seller.business_details.first()
        buyer = User.objects.filter(
            phone_number=data.get("phone_number"), user_type__contains="BUYER"
        ).first()
        if buyer:
            return Response(
                {
                    "detail": f"User already exist with number {data.get('phone_number')}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            buyer_serializer = self.serializer_class(data=data)
            buyer_serializer.is_valid(raise_exception=True)
            buyer = buyer_serializer.save()

            instance = BusinessCustomers.objects.create(
                status="Accept", business=business, customer=buyer
            )
            notification_data = {}
            notification_data["sender_id"] = seller.id
            notification_data["title"] = "New Notification From backend"
            notification_data[
                "body"
            ] = f"{instance.customer.first_name} is now member of your business."
            notification_data["receiver_id"] = instance.business.customer.id

            push_notification(
                notification_data=notification_data,
                user=instance.business.customer.id,
                send_to="SELLER",
            )
            Notifications.objects.create(
                sender_id=notification_data["sender_id"],
                receiver_id=notification_data["receiver_id"],
                message=notification_data["body"],
                notification_type="request_customer",
                updated_by_id=request.user.id,
            )

        return Response(
            CreateCustomerSerializers(buyer, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


from rest_framework.renderers import TemplateHTMLRenderer


class ProductDetailsPDfView(APIView):
    queryset = Products.objects.all()
    permission_classes = [IsAuthenticated]
    template_name = "product_list.html"
    renderer_classes = [TemplateHTMLRenderer]

    def get_queryset(self):
        if not self.request.user.is_anonymous:
            return (
                self.queryset.filter(
                    Q(business__customer=self.request.user.id)
                    | Q(business__staff=self.request.user.id)
                )
                .order_by("-created_at")
                .select_related("business")
                .annotate(Count("id"))
            )

    def get(self, request, *args, **kwargs):
        collection_id = self.request.query_params.get("collection_id")
        if collection_id:
            queryset = self.get_queryset().filter(collections=collection_id)
        else:
            queryset = self.get_queryset()

        business = (
            BusinessDetail.objects.filter(is_deleted=False)
            .filter(Q(customer=request.user.id) | Q(staff=request.user.id))
            .first()
        )

        business_name = None
        phone_number = None
        owner_name = None

        if business:

            business_name = business.business_name
            phone_number = business.phone_number
            owner_name = business.owner_name
        if bool(settings.USE_AWS_S3):
            server_url = "https://backend-media.s3.ap-south-1.amazonaws.com"
        else:
            server_url = f"{ request.scheme }://{ request.META['HTTP_HOST'] }"
        context = {
            "queryset": queryset,
            "business_name": business_name,
            "phone_number": phone_number,
            "owner_name": owner_name,
            "request": request,
            "server_url": server_url,
        }
        return Response(context)
