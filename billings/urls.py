from django.urls import path

from . import views

app_name = "billings"

urlpatterns = [
    # Subscription
    path(
        "subscription/",
        views.SubscriptionDetailView.as_view(),
        name="subscription-detail",
    ),
    path("overview/", views.billing_overview, name="billing-overview"),
    # Invoices
    path("invoices/", views.InvoiceListView.as_view(), name="invoice-list"),
    path(
        "invoices/<uuid:pk>/", views.InvoiceDetailView.as_view(), name="invoice-detail"
    ),
    # Usage Metrics
    path("usage/", views.UsageMetricListView.as_view(), name="usage-metric-list"),
    # Payment Methods
    path(
        "payment-methods/",
        views.PaymentMethodListView.as_view(),
        name="payment-method-list",
    ),
    path(
        "payment-methods/<uuid:pk>/",
        views.PaymentMethodDetailView.as_view(),
        name="payment-method-detail",
    ),
]
