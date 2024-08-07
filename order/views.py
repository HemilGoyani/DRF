from datetime import date
from datetime import datetime

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Count
from django.db.models import F
from django.db.models import Q
from django.db.models import Sum
from django.template.loader import render_to_string
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework import status
from rest_framework import views
from rest_framework.generics import GenericAPIView
from rest_framework.generics import ListAPIView
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from seller.models import BusinessCustomers
from seller.models import Notifications
from seller.models import Products
from seller.models import User
from seller.utils import PaginationClass
from seller.utils import push_notification

from .models import Order
from .models import OrderDetail
from .models import OrderProduct
from .serializers import CreateOrderSerializer
from .serializers import OrderSerializers
from .serializers import TrackOrderSerializer


class OrdersView(ListAPIView, GenericAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PaginationClass
    serializer_class = OrderSerializers

    def get_queryset(self):
        queryset = Order.objects.all()
        today = date.today()
        if not self.request.user.is_anonymous:
            order_status = self.request.query_params.get("order_status", None)
            seller_type = self.request.query_params.get("seller_type", None)
            if "SELLER" in seller_type.upper():
                queryset = (
                    queryset.filter(
                        Q(business_id__staff=self.request.user.id)
                        | Q(business_id__customer=self.request.user.id)
                    )
                    .annotate(Count("id"))
                    .order_by("-created_at")
                )
            elif "BUYER" in seller_type.upper():
                queryset = queryset.filter(customer=self.request.user).order_by(
                    "-created_at"
                )
                if order_status:
                    queryset = queryset.filter(status=order_status)
            from_date = self.request.query_params.get("from_date", None)
            to_date = self.request.query_params.get("to_date", None)
            if from_date and to_date:
                queryset = queryset.filter(
                    (
                        Q(created_at__date__gte=from_date)
                        & Q(created_at__date__lte=to_date)
                    )
                )
            sort = self.request.query_params.get("sort", None)
            if order_status == "pending":
                queryset = queryset.filter(status__in=["Placed", "Processing"])
                from_date = self.request.query_params.get("froDmate", None)
                to_date = self.request.query_params.get("toDate", None)
                if from_date and to_date:
                    queryset = queryset.filter(
                        (
                            Q(created_at__date__gte=from_date)
                            & Q(created_at__date__lte=to_date)
                        )
                    )
                order_type = self.request.query_params.get("order_type", None)
                if order_type:
                    queryset = queryset.filter(status=order_type)
            if order_status == "recent":
                queryset = queryset.filter(created_at__date=today)
            if sort:
                queryset = queryset.filter(status=sort)
            return queryset.order_by("-created_at")

    def get(self, request, *args, **kwargs):
        seller_type = self.request.query_params.get("seller_type", None)
        if not seller_type:
            return Response(
                {
                    "detail": "Value seller_type is missing or invalid; value should be 'SELLER or BUYER'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self.list(request, *args, **kwargs)


class OrderDetailView(GenericAPIView):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializers

    def get(self, request, order_id, *args, **kwargs):
        instance = self.get_queryset().filter(id=order_id).first()
        if instance:
            serializer = self.serializer_class(
                instance=instance, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"detail": "Order Not Found"}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, order_id, *args, **kwargs):
        instance = self.get_queryset().filter(id=order_id).first()
        if instance:
            data = request.data
            data.update({"updated_by": request.user.id})
            serializer = self.serializer_class(
                instance=instance,
                data=request.data,
                context={"order": instance, "request": request},
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            if data.get("status") == "Shipped":
                emailSubject = f"Your order has been successfully delivered"
                text_content = f"order"

                user_email = instance.customer.email

                context = {
                    "server_ip": f"{ request.scheme }://{ request.META['HTTP_HOST'] }",
                    "email": user_email,
                    "order": order_id,
                    "user": instance.customer,
                }

                html_content = render_to_string("order_delivered.html", context)

                if user_email:
                    emailMessage = EmailMultiAlternatives(
                        subject=emailSubject,
                        body=text_content,
                        from_email=settings.EMAIL_HOST_USER,
                        to=[
                            "met@taglineinfotech.com",  # user_email,
                        ],
                    )
                    emailMessage.attach_alternative(html_content, "text/html")
                    emailMessage.send(fail_silently=False)

            notification_data = {}
            notification_data["sender_id"] = request.user.id
            notification_data["title"] = "New Notification From backend"
            notification_data["body"] = f"Your Order is in {data['status']} stage."
            notification_data["receiver_id"] = instance.customer.id
            notification_data["order_id"] = order_id
            notifications = push_notification(
                notification_data=notification_data, user=instance.customer.id
            )
            for notification in notifications:
                Notifications.objects.create(
                    sender_id=notification_data["sender_id"],
                    receiver_id=notification_data["receiver_id"],
                    order_id=notification_data["order_id"],
                    message=notification_data["body"],
                    notification_type="order",
                    updated_by_id=request.user.id,
                )
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response({"detail": "Order Not Found"}, status=status.HTTP_404_NOT_FOUND)


class OrderTrackView(GenericAPIView):
    queryset = OrderDetail.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = TrackOrderSerializer

    def get(self, request, order_id, *args, **kwargs):
        instance = self.get_queryset().filter(order_id=order_id).order_by("-created_at")
        if instance:
            serializer = self.serializer_class(
                instance=instance, many=True, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"detail": "Order Not Found"}, status=status.HTTP_404_NOT_FOUND)


class OrderFilterView(ListCreateAPIView, views.APIView):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = PaginationClass
    serializer_class = OrderSerializers
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["total_amount", "created_at"]

    user_type = openapi.Parameter(
        "user_type",
        openapi.IN_QUERY,
        required=False,
        description="User Type",
        type=openapi.TYPE_STRING,
    )

    @swagger_auto_schema(manual_parameters=[user_type])
    # Filter for buyer-seller,from-date,to-date,sorting as order wise
    def get_queryset(self):
        queryset = (
            Order.objects.filter(
                Q(business_id__staff=self.request.user.id)
                | Q(business_id__customer=self.request.user.id)
            )
            .annotate(Count("id"))
            .order_by("-created_at")
        )

        if not self.request.user.is_anonymous:
            user_type = self.request.query_params.get("user_type", None)
            if user_type:
                user_type = user_type.upper()
            from_date = self.request.query_params.get("from_date", None)
            to_date = self.request.query_params.get("to_date", None)
            sort = self.request.query_params.get("sort", None)
            search = self.request.query_params.get("search", None)
            if search:
                queryset = queryset.filter(
                    Q(customer__first_name__contains=search)
                    | Q(customer__last_name__contains=search)
                    | Q(status=search)
                    | Q(customer__business_name__contains=search)
                )
            if user_type and "SELLER" in user_type:
                queryset = queryset.filter(
                    Q(created_by=self.request.user.id)
                    | Q(business_id__staff=self.request.user.id)
                ).annotate(Count("id"))
            if user_type and "BUYER" in user_type:
                queryset = queryset.filter(
                    created_by__user_type__contains="BUYER",
                    business_id__customer_id=self.request.user.id,
                )
            if from_date and to_date:
                queryset = queryset.filter(
                    (
                        Q(created_at__date__gte=from_date)
                        & Q(created_at__date__lte=to_date)
                    )
                )
            if sort:
                queryset = queryset.filter(status=sort)
            return queryset


# Recent orders and orders count


class HomeModuleOrderCount(GenericAPIView):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializers

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
            )

    def get(self, request, *args, **kwargs):
        today = date.today()
        total_customer = BusinessCustomers.objects.filter(
            (
                Q(business_id__customer=self.request.user.id)
                | Q(business_id__staff=self.request.user.id)
            )
            & Q(status="Accept")
        ).annotate(Count("id"))
        total_product = (
            Products.objects.filter(
                (
                    Q(business_id__customer=self.request.user.id)
                    | Q(business_id__staff=self.request.user.id)
                )
            )
            .annotate(Count("id"))
            .count()
        )

        total_orders = self.get_queryset().filter(created_at__year=today.year)
        recent_orders = (
            self.get_queryset().filter(created_at__date=today).order_by("-created_at")
        )
        pending_order = self.get_queryset().filter(
            created_at__year=today.year,
            status__in=["Placed", "Processing"],
        )
        serializer = self.serializer_class(
            instance=recent_orders, many=True, context={"request": request}
        )
        return Response(
            {
                "total_orders": len(total_orders),
                "total_customers": len(total_customer),
                "recent_orders": len(recent_orders),
                "pending_orders": len(pending_order),
                "total_product": total_product,
                "data": serializer.data,
            }
        )


class CreateOrderView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CreateOrderSerializer

    user_id = openapi.Parameter(
        "user_id", openapi.IN_QUERY, required=True, type=openapi.TYPE_STRING
    )

    @swagger_auto_schema(
        operation_description="Pass array of object like: [{product:x, quantity:x}]",
        manual_parameters=[user_id],
    )
    def post(self, request, *args, **kwargs):
        order_data = request.data
        total_amount, count = 0, 0
        list_to_create = []
        user_id = self.request.query_params.get("user_id")
        if user_id:
            user_obj = User.objects.filter(is_deleted=False, id=user_id).first()
            note = None
        for order_dict in order_data:
            for key, val in order_dict.items():
                if key == "product":
                    product_id = val
                elif key == "quantity":
                    quantity = val
                elif key == "lmitate":
                    lmitate = val
                elif key == "note":
                    note = val

            product = Products.objects.filter(id=product_id).first()
            if product:
                if count == 0:
                    order = Order.objects.create(
                        created_by=request.user,
                        customer=user_obj if user_id else request.user,
                        business=product.business,
                        total_amount=total_amount,
                        status="Placed",
                        updated_by=request.user,
                    )
                    OrderDetail.objects.create(
                        order=order, status="Placed", updated_by=request.user
                    )
                    count += 1

                total_amount += product.price * quantity
                list_to_create.append(
                    OrderProduct(
                        order=order,
                        product=product,
                        business=product.business,
                        quantity=quantity,
                        amount=product.price,
                        lmitate=lmitate,
                        updated_by=request.user,
                    )
                )
            else:
                return Response(
                    {"detail": "Invalid product id"}, status=status.HTTP_400_BAD_REQUEST
                )
        order.total_amount = total_amount
        order.note = note
        order.save()
        order_product_instance = OrderProduct.objects.bulk_create(list_to_create)
        response = OrderSerializers(order, context={"request": request})

        order_product_queryset = OrderProduct.objects.filter(
            id__in=[order_product.id for order_product in order_product_instance]
        ).annotate(total_amount=Sum(F("amount") * F("quantity")))

        emailSubject = f"Order summary"
        text_content = f"order"

        user_email = order.customer.email

        context = {
            "products": order_product_queryset,
            "server_ip": f"{ request.scheme }://{ request.META['HTTP_HOST'] }",
            "total_amount": total_amount,
            "order": order,
            "user": order.customer,
        }

        html_content = render_to_string("order_summary.html", context)

        if user_email:
            emailMessage = EmailMultiAlternatives(
                subject=emailSubject,
                body=text_content,
                from_email=settings.EMAIL_HOST_USER,
                to=[
                    "met@taglineinfotech.com",  # user_email,
                ],
            )
            emailMessage.attach_alternative(html_content, "text/html")
            emailMessage.send(fail_silently=False)

        notification_data = {}
        notification_data["sender_id"] = request.user.id
        notification_data["title"] = "New Notification From backend"
        notification_data[
            "body"
        ] = f"The order has been placed by {product.business.business_name if user_id else request.user.first_name}"
        notification_data["receiver_id"] = user_id
        notification_data["order_id"] = order.id
        notification_send_to = user_id
        if not user_id:
            notification_data["receiver_id"] = order.business.customer.id
            notification_send_to = order.business.customer.id

        push_notification(
            notification_data=notification_data,
            user=notification_send_to,
            send_to="SELLER",
        )
        Notifications.objects.create(
            sender_id=notification_data["sender_id"],
            receiver_id=notification_data["receiver_id"],
            order_id=notification_data["order_id"],
            message=notification_data["body"],
            notification_type="order",
            updated_by_id=request.user.id,
        )

        return Response(response.data, status=status.HTTP_201_CREATED)
