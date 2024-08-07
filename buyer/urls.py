from django.urls import path

from seller.views import SendOTP
from seller.views import VerifyOTP

from . import views

urlpatterns = [
    path("send-otp/", SendOTP.as_view(), name="buyer-send-otp"),
    path("verify-otp/", VerifyOTP.as_view(), name="buyer-verify-otp"),
    path("customer/", views.CustomerView.as_view(), name="create-customer"),
    path(
        "customer-detail/", views.CustomerDetailView.as_view(), name="customer-detail"
    ),
    path(
        "business-product/<int:business_id>",
        views.BusinessProductsView.as_view(),
        name="business-products",
    ),
    path(
        "business-details/",
        views.AllBusinessDetailView.as_view(),
        name="all-business-details",
    ),
    path("deals/", views.AllPromotedProducts.as_view(), name="promote-product"),
    path(
        "notification/", views.BuyerNotification.as_view(), name="seller-notification"
    ),
    path(
        "notification/<int:notification_id>",
        views.UpdateBuyerNotification.as_view(),
        name="seller-notification",
    ),
    path(
        "add-customer/", views.DirectAddCustomer.as_view(), name="direct-add-customer"
    ),
    path(
        "collection/<int:business_id>",
        views.BusinessCollectionView.as_view(),
        name="business_collection",
    ),
    path(
        "collection-product/<int:colection_id>",
        views.CollectionProductView.as_view(),
        name="collection-product",
    ),
]
