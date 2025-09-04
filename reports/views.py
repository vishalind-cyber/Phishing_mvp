from django.db.models import Avg, Count
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from users.permissions import CanViewReports

from .models import CampaignReport, DepartmentReport, ScheduledReport
from .serializers import (
    CampaignReportSerializer,
    DepartmentReportSerializer,
    ScheduledReportSerializer,
)


class CampaignReportListView(generics.ListAPIView):
    serializer_class = CampaignReportSerializer
    permission_classes = [CanViewReports]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["campaign__status"]
    ordering_fields = ["last_updated", "delivery_rate", "open_rate", "click_rate"]
    ordering = ["-last_updated"]

    def get_queryset(self):
        return CampaignReport.objects.filter(
            campaign__organization=self.request.user.organization
        ).select_related("campaign")


class CampaignReportDetailView(generics.RetrieveAPIView):
    serializer_class = CampaignReportSerializer
    permission_classes = [CanViewReports]

    def get_queryset(self):
        return CampaignReport.objects.filter(
            campaign__organization=self.request.user.organization
        ).select_related("campaign")


class DepartmentReportListView(generics.ListAPIView):
    serializer_class = DepartmentReportSerializer
    permission_classes = [CanViewReports]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["department", "campaign"]
    search_fields = ["department"]
    ordering_fields = ["risk_score", "improvement_percentage", "created_at"]
    ordering = ["-risk_score"]

    def get_queryset(self):
        return DepartmentReport.objects.filter(
            organization=self.request.user.organization
        ).select_related("campaign")


class ScheduledReportListView(generics.ListCreateAPIView):
    serializer_class = ScheduledReportSerializer
    permission_classes = [CanViewReports]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["report_type", "frequency", "is_active"]
    search_fields = ["name"]
    ordering = ["name"]

    def get_queryset(self):
        return (
            ScheduledReport.objects.filter(organization=self.request.user.organization)
            .select_related("created_by")
            .prefetch_related("include_campaigns")
        )


class ScheduledReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ScheduledReportSerializer
    permission_classes = [CanViewReports]

    def get_queryset(self):
        return ScheduledReport.objects.filter(
            organization=self.request.user.organization
        )


@swagger_auto_schema(method="get", responses={200: "Organization statistics"})
@api_view(["GET"])
@permission_classes([CanViewReports])
def organization_statistics(request):
    """Get comprehensive organization statistics"""
    org = request.user.organization

    from campaigns.models import Campaign, CampaignTarget
    from targets.models import Target

    # Campaign statistics
    campaigns = Campaign.objects.filter(organization=org)
    campaign_targets = CampaignTarget.objects.filter(campaign__organization=org)

    stats = {
        "overview": {
            "total_campaigns": campaigns.count(),
            "active_campaigns": campaigns.filter(
                status__in=["running", "scheduled"]
            ).count(),
            "total_targets": Target.objects.filter(organization=org).count(),
            "total_emails_sent": campaign_targets.exclude(
                email_sent_at__isnull=True
            ).count(),
        },
        "campaign_performance": {
            "average_open_rate": CampaignReport.objects.filter(
                campaign__organization=org
            ).aggregate(avg=Avg("open_rate"))["avg"]
            or 0,
            "average_click_rate": CampaignReport.objects.filter(
                campaign__organization=org
            ).aggregate(avg=Avg("click_rate"))["avg"]
            or 0,
            "average_susceptibility_rate": CampaignReport.objects.filter(
                campaign__organization=org
            ).aggregate(avg=Avg("susceptibility_rate"))["avg"]
            or 0,
        },
        "department_breakdown": list(
            DepartmentReport.objects.filter(organization=org)
            .values("department")
            .annotate(
                avg_risk_score=Avg("risk_score"),
                total_employees=Count("total_employees"),
            )
            .order_by("-avg_risk_score")[:10]
        ),
        "recent_activity": {
            "campaigns_this_month": campaigns.filter(
                created_at__gte=timezone.now().replace(day=1)
            ).count(),
            "emails_sent_this_month": campaign_targets.filter(
                email_sent_at__gte=timezone.now().replace(day=1)
            ).count(),
        },
    }

    return Response(stats)
