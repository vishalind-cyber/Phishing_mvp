from django.urls import include, path

urlpatterns = [
    # Users and Authentication
    path("", include("users.urls")),
    path("targets/", include("targets.urls")),
    path("campaign/", include("campaigns.urls")),
    path("reports/", include("reports.urls")),
    path("notifications/", include("notifications.urls")),
    path("billings/", include("billings.urls")),
    path("emails/", include("emails.urls")),
]
