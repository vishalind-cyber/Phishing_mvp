from django.db.models import Count, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from users.permissions import (
    CanManageCampaigns,
    CanManageEmailTemplates,
    IsOrganizationMember,
)
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Campaign, CampaignTarget, EmailTemplate, LandingPage
from .serializers import (
    CampaignCreateSerializer,
    CampaignSerializer,
    CampaignTargetSerializer,
    EmailTemplateSerializer,
    LandingPageSerializer,
)


class EmailTemplateListView(generics.ListCreateAPIView):
    serializer_class = EmailTemplateSerializer
    permission_classes = [CanManageEmailTemplates]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["template_type", "difficulty_level", "is_default"]
    search_fields = ["name", "subject", "sender_name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        return EmailTemplate.objects.filter(
            organization=self.request.user.organization
        ).select_related("created_by")


class EmailTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmailTemplateSerializer
    permission_classes = [CanManageEmailTemplates]

    def get_queryset(self):
        return EmailTemplate.objects.filter(
            organization=self.request.user.organization
        ).select_related("created_by")


class LandingPageListView(generics.ListCreateAPIView):
    serializer_class = LandingPageSerializer
    permission_classes = [CanManageCampaigns]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["page_type", "capture_credentials", "capture_form_data"]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        return LandingPage.objects.filter(
            organization=self.request.user.organization
        ).select_related("created_by")


class LandingPageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LandingPageSerializer
    permission_classes = [CanManageCampaigns]

    def get_queryset(self):
        return LandingPage.objects.filter(
            organization=self.request.user.organization
        ).select_related("created_by")


class CampaignListView(generics.ListCreateAPIView):
    permission_classes = [CanManageCampaigns]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "template__template_type"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at", "scheduled_start"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Campaign.objects.filter(organization=self.request.user.organization)
            .select_related("template", "landing_page", "created_by")
            .prefetch_related("target_groups", "individual_targets", "campaign_targets")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CampaignCreateSerializer
        return CampaignSerializer

    # 🔑 This ensures request is always passed into serializer context
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class CampaignDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CampaignSerializer
    permission_classes = [CanManageCampaigns]

    def get_queryset(self):
        return (
            Campaign.objects.filter(organization=self.request.user.organization)
            .select_related("template", "landing_page", "created_by")
            .prefetch_related("target_groups", "individual_targets", "campaign_targets")
        )


class CampaignActionView(APIView):
    permission_classes = [CanManageCampaigns]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "action": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["start", "pause", "resume", "cancel"],
                )
            },
        ),
        responses={200: "Action completed successfully"},
    )
    def post(self, request, pk):
        try:
            campaign = Campaign.objects.get(
                pk=pk, organization=request.user.organization
            )
        except Campaign.DoesNotExist:
            return Response(
                {"error": "Campaign not found"}, status=status.HTTP_404_NOT_FOUND
            )

        action = request.data.get("action")

        if action == "start":
            if campaign.status != "draft":
                return Response(
                    {"error": "Only draft campaigns can be started"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            campaign.status = "running"
            campaign.actual_start = timezone.now()

        elif action == "pause":
            if campaign.status != "running":
                return Response(
                    {"error": "Only running campaigns can be paused"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            campaign.status = "paused"

        elif action == "resume":
            if campaign.status != "paused":
                return Response(
                    {"error": "Only paused campaigns can be resumed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            campaign.status = "running"

        elif action == "cancel":
            if campaign.status not in ["draft", "scheduled", "running", "paused"]:
                return Response(
                    {"error": "Campaign cannot be cancelled"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            campaign.status = "cancelled"
            campaign.end_date = timezone.now()

        else:
            return Response(
                {"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST
            )

        campaign.save()

        return Response(
            {
                "message": f"Campaign {action}ed successfully",
                "campaign": CampaignSerializer(campaign).data,
            }
        )


class CampaignTargetsView(generics.ListAPIView):
    serializer_class = CampaignTargetSerializer
    permission_classes = [CanManageCampaigns]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status"]
    search_fields = ["target__first_name", "target__last_name", "target__email"]
    ordering_fields = ["target__last_name", "email_sent_at", "status"]
    ordering = ["target__last_name"]

    def get_queryset(self):
        campaign_id = self.kwargs["campaign_id"]
        return CampaignTarget.objects.filter(
            campaign_id=campaign_id,
            campaign__organization=self.request.user.organization,
        ).select_related("target", "campaign")


class CampaignReportsView(APIView):
    permission_classes = [CanManageCampaigns]

    @swagger_auto_schema(responses={200: "Campaign statistics"})
    def get(self, request, pk):
        try:
            campaign = Campaign.objects.get(
                pk=pk, organization=request.user.organization
            )
        except Campaign.DoesNotExist:
            return Response(
                {"error": "Campaign not found"}, status=status.HTTP_404_NOT_FOUND
            )

        targets = campaign.campaign_targets.all()

        stats = {
            "campaign_info": {
                "id": campaign.id,
                "name": campaign.name,
                "status": campaign.status,
                "created_at": campaign.created_at,
                "actual_start": campaign.actual_start,
                "end_date": campaign.end_date,
            },
            "email_stats": {
                "total_targets": targets.count(),
                "emails_sent": targets.exclude(email_sent_at__isnull=True).count(),
                "emails_delivered": targets.filter(
                    status__in=["sent", "opened", "clicked", "submitted"]
                ).count(),
                "emails_opened": targets.exclude(email_opened_at__isnull=True).count(),
                "links_clicked": targets.exclude(link_clicked_at__isnull=True).count(),
                "data_submitted": targets.exclude(
                    data_submitted_at__isnull=True
                ).count(),
                "emails_reported": targets.exclude(reported_at__isnull=True).count(),
            },
            "status_breakdown": {
                "pending": targets.filter(status="pending").count(),
                "sent": targets.filter(status="sent").count(),
                "opened": targets.filter(status="opened").count(),
                "clicked": targets.filter(status="clicked").count(),
                "submitted": targets.filter(status="submitted").count(),
                "reported": targets.filter(status="reported").count(),
                "failed": targets.filter(status="failed").count(),
            },
        }

        # Calculate rates
        total_sent = stats["email_stats"]["emails_sent"]
        if total_sent > 0:
            stats["rates"] = {
                "open_rate": round(
                    (stats["email_stats"]["emails_opened"] / total_sent) * 100, 2
                ),
                "click_rate": round(
                    (stats["email_stats"]["links_clicked"] / total_sent) * 100, 2
                ),
                "submission_rate": round(
                    (stats["email_stats"]["data_submitted"] / total_sent) * 100, 2
                ),
                "report_rate": round(
                    (stats["email_stats"]["emails_reported"] / total_sent) * 100, 2
                ),
            }
        else:
            stats["rates"] = {
                "open_rate": 0,
                "click_rate": 0,
                "submission_rate": 0,
                "report_rate": 0,
            }

        return Response(stats)


@swagger_auto_schema(
    method="get",
    responses={200: "Campaign statistics"},
    operation_description="Get overall campaign statistics for dashboard",
)
@api_view(["GET"])
@permission_classes([CanManageCampaigns])
def campaign_statistics(request):
    """Get campaign statistics for dashboard"""
    organization = request.user.organization
    campaigns_queryset = Campaign.objects.filter(organization=organization)

    stats = {
        "total_campaigns": campaigns_queryset.count(),
        "campaigns_by_status": {
            "draft": campaigns_queryset.filter(status="draft").count(),
            "scheduled": campaigns_queryset.filter(status="scheduled").count(),
            "running": campaigns_queryset.filter(status="running").count(),
            "paused": campaigns_queryset.filter(status="paused").count(),
            "completed": campaigns_queryset.filter(status="completed").count(),
            "cancelled": campaigns_queryset.filter(status="cancelled").count(),
        },
        "template_stats": {
            "total_templates": EmailTemplate.objects.filter(
                organization=organization
            ).count(),
            "templates_by_type": list(
                EmailTemplate.objects.filter(organization=organization)
                .values("template_type")
                .annotate(count=Count("template_type"))
                .order_by("-count")
            ),
        },
        "landing_page_stats": {
            "total_pages": LandingPage.objects.filter(
                organization=organization
            ).count(),
            "pages_by_type": list(
                LandingPage.objects.filter(organization=organization)
                .values("page_type")
                .annotate(count=Count("page_type"))
                .order_by("-count")
            ),
        },
    }

    return Response(stats)
