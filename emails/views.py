from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from users.permissions import CanManageCampaigns, IsOrganizationAdmin

from .models import EmailEvent, EmailQueue, SMTPConfiguration
from .serializers import (
    EmailEventSerializer,
    EmailQueueSerializer,
    SMTPConfigurationSerializer,
)


class SMTPConfigurationListView(generics.ListCreateAPIView):
    serializer_class = SMTPConfigurationSerializer
    permission_classes = [IsOrganizationAdmin]
    ordering = ["name"]

    def get_queryset(self):
        return SMTPConfiguration.objects.filter(
            organization=self.request.user.organization
        )


class SMTPConfigurationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SMTPConfigurationSerializer
    permission_classes = [IsOrganizationAdmin]

    def get_queryset(self):
        return SMTPConfiguration.objects.filter(
            organization=self.request.user.organization
        )


class EmailQueueListView(generics.ListAPIView):
    serializer_class = EmailQueueSerializer
    permission_classes = [CanManageCampaigns]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status", "campaign"]
    ordering = ["-scheduled_time"]

    def get_queryset(self):
        return EmailQueue.objects.filter(
            campaign__organization=self.request.user.organization
        ).select_related("campaign", "target")


class EmailEventListView(generics.ListAPIView):
    serializer_class = EmailEventSerializer
    permission_classes = [CanManageCampaigns]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["event_type", "campaign"]
    search_fields = ["target__email", "ip_address"]
    ordering = ["-timestamp"]

    def get_queryset(self):
        return EmailEvent.objects.filter(
            campaign__organization=self.request.user.organization
        ).select_related("campaign", "target")


@swagger_auto_schema(method="get", responses={200: "Email statistics"})
@api_view(["GET"])
@permission_classes([CanManageCampaigns])
def email_statistics(request):
    """Get email statistics for organization"""
    org = request.user.organization

    from datetime import timedelta

    from django.db.models import Count
    from django.utils import timezone

    # Get email events for the organization
    events = EmailEvent.objects.filter(campaign__organization=org)
    queue = EmailQueue.objects.filter(campaign__organization=org)

    stats = {
        "email_volume": {
            "total_emails_queued": queue.count(),
            "emails_sent": queue.filter(status="sent").count(),
            "emails_failed": queue.filter(status="failed").count(),
            "emails_pending": queue.filter(status="queued").count(),
        },
        "event_breakdown": dict(
            events.values("event_type")
            .annotate(count=Count("event_type"))
            .values_list("event_type", "count")
        ),
        "recent_activity": {
            "emails_sent_today": queue.filter(
                sent_time__gte=timezone.now().date()
            ).count(),
            "emails_sent_this_week": queue.filter(
                sent_time__gte=timezone.now() - timedelta(days=7)
            ).count(),
            "events_today": events.filter(timestamp__gte=timezone.now().date()).count(),
        },
        "smtp_configurations": SMTPConfiguration.objects.filter(
            organization=org, is_active=True
        ).count(),
    }

    return Response(stats)
