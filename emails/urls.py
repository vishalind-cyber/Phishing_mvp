from django.urls import path

from . import views

app_name = "emails"

urlpatterns = [
    # SMTP Configuration
    path(
        "smtp-configs/",
        views.SMTPConfigurationListView.as_view(),
        name="smtp-config-list",
    ),
    path(
        "smtp-configs/<uuid:pk>/",
        views.SMTPConfigurationDetailView.as_view(),
        name="smtp-config-detail",
    ),
    # Email Queue
    path("queue/", views.EmailQueueListView.as_view(), name="email-queue-list"),
    # Email Events
    path("events/", views.EmailEventListView.as_view(), name="email-event-list"),
    # Statistics
    path("statistics/", views.email_statistics, name="email-statistics"),
]
