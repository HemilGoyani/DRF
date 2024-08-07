from django.urls import path

from order.views import OrderFilterView

from . import views

urlpatterns = [
    path("send-otp/", views.SendOTP.as_view(), name="login"),
    path("verify-otp/", views.VerifyOTP.as_view(), name="verify"),
    path("business-detail/", views.BusinessCreate.as_view(), name="business-details"),
    path(
        "business-detail/<int:business_id>",
        views.BusinessDetails.as_view(),
        name="business-detail",
    ),
    path("customer/", views.AllCustomerDetails.as_view(), name="customer-detail"),
    path("group-detail/", views.GroupDetailView.as_view(), name="group-details"),
    path("group-detail/<int:group_id>", views.GroupView.as_view(), name="group-detail"),
    path("staff-details/", views.StaffDetailsView.as_view(), name="staff-details"),
    path(
        "staff-detail/<int:staff_id>", views.StaffDetail.as_view(), name="staff-detail"
    ),
    path("product-details/", views.ProductsView.as_view(), name="product-create"),
    path(
        "product-detail/<int:product_id>",
        views.ProductDetailView.as_view(),
        name="product-detail",
    ),
    path("promotion-details/", views.PromotionView.as_view(), name="promotion-detail"),
    path("order-filter/", OrderFilterView.as_view(), name="promotion-detail"),
    path("request-user/", views.RequestCustomer.as_view(), name="request-user"),
    path(
        "notification/", views.SellerNotification.as_view(), name="seller-notification"
    ),
    path("collection/", views.CollectionListCreateView.as_view(), name="collection"),
    path(
        "collection/<int:collection_id>/",
        views.CollectionRetrieveDestroyAPIView.as_view(),
        name="get-delete-collection",
    ),
    path(
        "edit-collection/<int:collection_id>/",
        views.CollectionEditAPIView.as_view(),
        name="collection-edit",
    ),
    path(
        "create-customer/",
        views.CreateCustomer.as_view(),
        name="create-customer",
    ),
    path(
        "product-details-pdf/",
        views.ProductDetailsPDfView.as_view(),
        name="product-details-pdf",
    ),
]
