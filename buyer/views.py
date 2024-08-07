from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.generics import ListAPIView
from rest_framework.generics import ListCreateAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from seller.models import BusinessCustomers
from seller.models import BusinessDetail
from seller.models import Collection
from seller.models import Group
from seller.models import Notifications
from seller.models import Products
from seller.models import User
from seller.serializers import BusinessDetailSerializers
from seller.serializers import NotificationSerializers
from seller.serializers import PromotionProductSerializers
from seller.utils import PaginationClass
from seller.utils import push_notification

from .serializers import BusinessCollectionSerializers
from .serializers import BusinessProductsSerializers
from .serializers import BusinessSerializer
from .serializers import CreateCustomerSerializers
from .serializers import DirectAddCustomerSerializers
from .serializers import NotificationDetailSerializers

# Create your views here.


class CustomerView(GenericAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = CreateCustomerSerializers

    def get_queryset(self):
        if not self.request.user.is_anonymous:
            return (
                super()
                .get_queryset()
                .filter(is_deleted=False, user_type__contains="BUYER")
                .order_by("-date_joined")
            )

    def post(self, request):
        user = (
            self.get_queryset().filter(phone_number=request.user.phone_number).first()
        )
        if user:
            data = request.data
            data._mutable = True
            data.update({"is_detail": True})
            serializer = self.serializer_class(
                instance=user,
                data=data,
                context={"request": request, "instance": user},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)


class CustomerDetailView(GenericAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = CreateCustomerSerializers

    def get_queryset(self):
        if not self.request.user.is_anonymous:
            return (
                super()
                .get_queryset()
                .filter(user_type__contains="BUYER", is_deleted=False)
            )

    def get(self, request, *args, **kwargs):
        user = self.get_queryset().filter(id=request.user.id).first()
        if user:
            serializer = self.serializer_class(
                instance=user, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, *args, **kwargs):
        data = self.get_queryset().filter(id=request.user.id).first()
        if data:
            serializer = self.serializer_class(
                instance=data,
                data=request.data,
                partial=True,
                context={"request": request, "instance": data},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response({}, status=status.HTTP_404_NOT_FOUND)


class BusinessProductsView(ListAPIView):
    queryset = BusinessDetail.objects.filter(is_deleted=False)
    pagination_class = PaginationClass
    permission_classes = [IsAuthenticated]
    serializer_class = BusinessProductsSerializers

    search = openapi.Parameter(
        "search",
        openapi.IN_QUERY,
        description="Search product by name.",
        type=openapi.TYPE_STRING,
    )

    @swagger_auto_schema(manual_parameters=[search])
    def get(self, request, business_id, *args, **kwargs):
        instance = self.get_queryset().filter(id=business_id).order_by("-created_at")
        if instance:
            search = self.request.query_params.get("search")
            serializer = self.serializer_class(
                instance=instance,
                many=True,
                context={"request": request, "search": search},
            )
            page = self.paginate_queryset(serializer.data)
            return self.get_paginated_response(page)
        return Response(
            {"detail": "Business Not Found"}, status=status.HTTP_404_NOT_FOUND
        )


class AllBusinessDetailView(ListCreateAPIView, GenericAPIView):
    queryset = BusinessDetail.objects.filter(is_deleted=False)
    pagination_class = PaginationClass
    permission_classes = [IsAuthenticated]
    serializer_class = BusinessDetailSerializers
    filter_backends = [filters.SearchFilter]
    search_fields = ["business_name"]

    def get_queryset(self):
        business = BusinessCustomers.objects.filter(
            customer=self.request.user.id, status="Accept"
        ).values_list("business", flat=True)
        return self.queryset.filter(id__in=business).order_by("-created_at")


class AllPromotedProducts(ListAPIView):
    queryset = BusinessDetail.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]
    pagination_class = PaginationClass
    serializer_class = BusinessSerializer

    def get_queryset(self):
        business_list = Group.objects.filter(customer=self.request.user).values_list(
            "business", flat=True
        )
        return super().get_queryset().filter(id__in=business_list)

    # def get_queryset(self):
    #     group_list = Group.objects.filter(customer=self.request.user).values_list("id", flat=True)
    #     # return super().get_queryset()

    #     from django.db.models import Count
    #     from datetime import datetime, timedelta
    #     # Promotion.objects.filter(group__in=group_list,
    #     #     created_at__gte=datetime.now() - timedelta(days=7)).values('business',
    #     #     'product').annotate(dcount=Count('business')).distinct()
    #     Promotion.objects.filter(group__in=group_list,
    #         created_at__gte=datetime.now() - timedelta(days=7)).annotate(business=Promotion.objects.filter(), products = Promotion.objects.filter())

    #     # Promotion.objects.filter(group__in=group_list,
    #     #     created_at__gte=datetime.now() - timedelta(days=7)).group_by().order_by("-created_at")


class BuyerNotification(ListCreateAPIView, GenericAPIView):
    queryset = Notifications.objects.all()
    pagination_class = PaginationClass
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationDetailSerializers

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                receiver_id=self.request.user.id, receiver__user_type__contains="BUYER"
            )
            .order_by("-created_at")
        )


class UpdateBuyerNotification(GenericAPIView):
    parser_classes = (MultiPartParser,)
    queryset = Notifications.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializers

    def patch(self, request, notification_id, *args, **kwargs):
        notification = (
            self.get_queryset()
            .filter(id=notification_id, receiver_id=request.user.id)
            .first()
        )
        if notification:
            serializer = self.serializer_class(
                instance=notification, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            instance = BusinessCustomers.objects.filter(
                customer=request.user.id, notification=notification.id, status="Pending"
            ).first()

            instance.status = request.data["status"]
            instance.save()
            notification_data = {}
            notification_data["sender_id"] = request.user.id
            notification_data["title"] = "New Notification From backend"
            notification_data[
                "body"
            ] = f"The request has been {request.data['status']}ed by the {request.user.first_name}."
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
                status=request.data["status"],
                notification_type="request_customer",
                updated_by_id=request.user.id,
            )

            if request.data["status"].upper() == "REJECT":
                instance.delete()

            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response({"detail": "Not Found"}, status=status.HTTP_404_NOT_FOUND)


class DirectAddCustomer(GenericAPIView):
    """
    Directly connect a buyer to seller without going through request accept flow.
    """

    queryset = BusinessCustomers.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = DirectAddCustomerSerializers

    def post(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        if data:
            data._mutable = True
        data.update({"status": "Accept", "updated_by": request.user.id})
        serializer = self.serializer_class(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        notification_data = {}
        notification_data["sender_id"] = user.id
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
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BusinessCollectionView(ListAPIView):
    queryset = Collection.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = PaginationClass
    serializer_class = BusinessCollectionSerializers

    def get(self, request, business_id, *args, **kwargs):
        self.queryset = super().get_queryset().filter(business=business_id)
        return self.list(request, *args, **kwargs)


class CollectionProductView(ListAPIView):
    queryset = Products.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = PaginationClass
    serializer_class = PromotionProductSerializers

    def get(self, request, colection_id, *args, **kwargs):
        collection = Collection.objects.filter(id=colection_id).first()
        if not collection:
            return Response(
                {"detail": "Collection Not found!"}, status=status.HTTP_404_NOT_FOUND
            )
        collection_product_id_list = collection.products.all().values_list(
            "id", flat=True
        )
        self.queryset = (
            super()
            .get_queryset()
            .exclude(status=Products.DISCONTINUED)
            .filter(id__in=collection_product_id_list)
        )
        return self.list(request, *args, **kwargs)
