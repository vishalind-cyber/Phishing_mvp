from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    # Notifications
    path("", views.NotificationListView.as_view(), name="notification-list"),
    path(
        "<uuid:pk>/", views.NotificationDetailView.as_view(), name="notification-detail"
    ),
    path(
        "<uuid:pk>/read/",
        views.MarkNotificationReadView.as_view(),
        name="mark-notification-read",
    ),
    path(
        "mark-all-read/",
        views.MarkAllNotificationsReadView.as_view(),
        name="mark-all-notifications-read",
    ),
    path("statistics/", views.notification_statistics, name="notification-statistics"),
    # Preferences
    path(
        "preferences/",
        views.NotificationPreferenceView.as_view(),
        name="notification-preferences",
    ),
    # Alert Rules
    path("alert-rules/", views.AlertRuleListView.as_view(), name="alert-rule-list"),
    path(
        "alert-rules/<uuid:pk>/",
        views.AlertRuleDetailView.as_view(),
        name="alert-rule-detail",
    ),
]
