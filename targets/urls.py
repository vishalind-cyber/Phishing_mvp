from django.urls import path

from . import views

app_name = "targets"

urlpatterns = [
    # Targets
    path("", views.TargetListView.as_view(), name="target-list"),
    path("<uuid:pk>/", views.TargetDetailView.as_view(), name="target-detail"),
    path(
        "bulk-create/", views.TargetBulkCreateView.as_view(), name="target-bulk-create"
    ),
    path("statistics/", views.target_statistics, name="target-statistics"),
    # Target Groups
    path("groups/", views.TargetGroupListView.as_view(), name="target-group-list"),
    path(
        "groups/<uuid:pk>/",
        views.TargetGroupDetailView.as_view(),
        name="target-group-detail",
    ),
    # Target Tags
    path("tags/", views.TargetTagListView.as_view(), name="target-tag-list"),
    path(
        "tags/<uuid:pk>/", views.TargetTagDetailView.as_view(), name="target-tag-detail"
    ),
    # Import History
    path("imports/", views.TargetImportListView.as_view(), name="target-import-list"),
]
