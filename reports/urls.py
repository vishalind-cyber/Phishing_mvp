from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    # Campaign Reports
    path(
        "campaigns/",
        views.CampaignReportListView.as_view(),
        name="campaign-report-list",
    ),
    path(
        "campaigns/<uuid:pk>/",
        views.CampaignReportDetailView.as_view(),
        name="campaign-report-detail",
    ),
    # Department Reports
    path(
        "departments/",
        views.DepartmentReportListView.as_view(),
        name="department-report-list",
    ),
    # Scheduled Reports
    path(
        "scheduled/",
        views.ScheduledReportListView.as_view(),
        name="scheduled-report-list",
    ),
    path(
        "scheduled/<uuid:pk>/",
        views.ScheduledReportDetailView.as_view(),
        name="scheduled-report-detail",
    ),
    # Statistics
    path("statistics/", views.organization_statistics, name="organization-statistics"),
]
