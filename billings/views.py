from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from users.permissions import CanAccessBilling

from .models import Invoice, PaymentMethod, Subscription, UsageMetric
from .serializers import (
    InvoiceSerializer,
    PaymentMethodSerializer,
    SubscriptionSerializer,
    UsageMetricSerializer,
)


class SubscriptionDetailView(generics.RetrieveAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [CanAccessBilling]

    def get_object(self):
        return self.request.user.organization.subscription


class InvoiceListView(generics.ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [CanAccessBilling]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status", "payment_method"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Invoice.objects.filter(
            organization=self.request.user.organization
        ).select_related("subscription")


class InvoiceDetailView(generics.RetrieveAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [CanAccessBilling]

    def get_queryset(self):
        return Invoice.objects.filter(organization=self.request.user.organization)


class UsageMetricListView(generics.ListAPIView):
    serializer_class = UsageMetricSerializer
    permission_classes = [CanAccessBilling]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["metric_type", "warning_sent", "limit_exceeded"]
    ordering = ["metric_type"]

    def get_queryset(self):
        return UsageMetric.objects.filter(organization=self.request.user.organization)


class PaymentMethodListView(generics.ListCreateAPIView):
    serializer_class = PaymentMethodSerializer
    permission_classes = [CanAccessBilling]
    ordering = ["-is_default", "-created_at"]

    def get_queryset(self):
        return PaymentMethod.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


class PaymentMethodDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PaymentMethodSerializer
    permission_classes = [CanAccessBilling]

    def get_queryset(self):
        return PaymentMethod.objects.filter(organization=self.request.user.organization)


@swagger_auto_schema(method="get", responses={200: "Billing overview"})
@api_view(["GET"])
@permission_classes([CanAccessBilling])
def billing_overview(request):
    """Get billing overview for organization"""
    org = request.user.organization

    try:
        subscription = org.subscription
        recent_invoices = Invoice.objects.filter(organization=org).order_by(
            "-created_at"
        )[:5]
        usage_metrics = UsageMetric.objects.filter(organization=org)

        overview = {
            "subscription": SubscriptionSerializer(subscription).data,
            "current_usage": UsageMetricSerializer(usage_metrics, many=True).data,
            "recent_invoices": InvoiceSerializer(recent_invoices, many=True).data,
            "billing_summary": {
                "total_invoices": Invoice.objects.filter(organization=org).count(),
                "paid_invoices": Invoice.objects.filter(
                    organization=org, status="paid"
                ).count(),
                "overdue_invoices": Invoice.objects.filter(
                    organization=org, status="overdue"
                ).count(),
                "outstanding_amount": sum(
                    invoice.total_amount
                    for invoice in Invoice.objects.filter(
                        organization=org, status__in=["sent", "overdue"]
                    )
                ),
            },
        }

        return Response(overview)

    except Subscription.DoesNotExist:
        return Response({"error": "No subscription found"}, status=404)
