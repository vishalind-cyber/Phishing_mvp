from django.urls import path
from . import views

app_name = "campaigns"

urlpatterns = [
    # Email Templates
    path("templates/", views.EmailTemplateListView.as_view(), name="template-list"),
    path(
        "templates/<uuid:pk>/",
        views.EmailTemplateDetailView.as_view(),
        name="template-detail",
    ),
    # Landing Pages
    path(
        "landing-pages/", views.LandingPageListView.as_view(), name="landing-page-list"
    ),
    path(
        "landing-pages/<uuid:pk>/",
        views.LandingPageDetailView.as_view(),
        name="landing-page-detail",
    ),
    # Campaigns
    path("", views.CampaignListView.as_view(), name="campaign-list"),
    path("<uuid:pk>/", views.CampaignDetailView.as_view(), name="campaign-detail"),
    path(
        "<uuid:pk>/action/", views.CampaignActionView.as_view(), name="campaign-action"
    ),
    path(
        "<uuid:pk>/reports/",
        views.CampaignReportsView.as_view(),
        name="campaign-reports",
    ),
    path(
        "<uuid:campaign_id>/targets/",
        views.CampaignTargetsView.as_view(),
        name="campaign-targets",
    ),
    # Statistics
    path("statistics/", views.campaign_statistics, name="campaign-statistics"),
]
