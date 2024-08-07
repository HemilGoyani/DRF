from django.urls import path

from . import views

urlpatterns = [
    path("order-details/", views.OrdersView.as_view(), name="order-view"),
    path(
        "order-detail/<int:order_id>/",
        views.OrderDetailView.as_view(),
        name="order-view",
    ),
    path(
        "track-order/<int:order_id>/",
        views.OrderTrackView.as_view(),
        name="track-order",
    ),
    path("recent-order/", views.HomeModuleOrderCount.as_view(), name="recent-order"),
    path("", views.CreateOrderView.as_view(), name="create-order"),
]
