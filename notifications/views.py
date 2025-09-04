from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import CanAccessNotifications, IsOrganizationMember

from .models import AlertRule, Notification, NotificationPreference
from .serializers import (
    AlertRuleSerializer,
    NotificationPreferenceSerializer,
    NotificationSerializer,
)


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [CanAccessNotifications]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["notification_type", "priority", "is_read"]
    search_fields = ["title", "message"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related(
            "campaign", "target"
        )


class NotificationDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [CanAccessNotifications]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class MarkNotificationReadView(APIView):
    permission_classes = [CanAccessNotifications]

    @swagger_auto_schema(responses={200: "Notification marked as read"})
    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, recipient=request.user)
            notification.mark_as_read()
            return Response({"message": "Notification marked as read"})
        except Notification.DoesNotExist:
            return Response(
                {"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND
            )


class MarkAllNotificationsReadView(APIView):
    permission_classes = [CanAccessNotifications]

    @swagger_auto_schema(responses={200: "All notifications marked as read"})
    def post(self, request):
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return Response({"message": f"{count} notifications marked as read"})


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [CanAccessNotifications]

    def get_object(self):
        preference, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preference


class AlertRuleListView(generics.ListCreateAPIView):
    serializer_class = AlertRuleSerializer
    permission_classes = [IsOrganizationMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["trigger_type", "is_active"]
    search_fields = ["name"]
    ordering = ["name"]

    def get_queryset(self):
        return AlertRule.objects.filter(
            organization=self.request.user.organization
        ).prefetch_related("notify_users", "created_by")


class AlertRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AlertRuleSerializer
    permission_classes = [IsOrganizationMember]

    def get_queryset(self):
        return AlertRule.objects.filter(organization=self.request.user.organization)


@swagger_auto_schema(method="get", responses={200: "Notification statistics"})
@api_view(["GET"])
@permission_classes([CanAccessNotifications])
def notification_statistics(request):
    """Get notification statistics for user"""
    user = request.user
    notifications = Notification.objects.filter(recipient=user)

    stats = {
        "total_notifications": notifications.count(),
        "unread_notifications": notifications.filter(is_read=False).count(),
        "notifications_by_type": dict(
            notifications.values("notification_type")
            .annotate(count=Count("notification_type"))
            .values_list("notification_type", "count")
        ),
        "notifications_by_priority": dict(
            notifications.values("priority")
            .annotate(count=Count("priority"))
            .values_list("priority", "count")
        ),
        "recent_notifications": notifications.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count(),
    }

    return Response(stats)
