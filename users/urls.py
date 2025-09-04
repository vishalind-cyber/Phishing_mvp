from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "users"

urlpatterns = [
    # Authentication
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path(
        "auth/change-password/",
        views.ChangePasswordView.as_view(),
        name="change-password",
    ),
    # User management
    path("profile/", views.UserProfileView.as_view(), name="user-profile"),
    path("users/", views.UserListView.as_view(), name="user-list"),
    path("users/<uuid:pk>/", views.UserDetailView.as_view(), name="user-detail"),
    path("statistics/", views.user_statistics, name="user-statistics"),
    # Organization management
    path(
        "organizations/",
        views.OrganizationListCreateView.as_view(),
        name="organization-list-create",
    ),
    path(
        "organizations/<uuid:pk>/",
        views.OrganizationDetailView.as_view(),
        name="organization-detail",
    ),
]
