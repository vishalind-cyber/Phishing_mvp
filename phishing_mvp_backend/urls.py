"""
URL configuration for phishing_mvp_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path, re_path
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

schema_view = get_schema_view(
    openapi.Info(
        title="Phishing Simulation API",
        default_version="v1",
        description="""
        A comprehensive API for managing phishing simulation campaigns.

        ## Features
        - User and Organization Management
        - Target Management with Groups and Tags
        - Email Template Creation
        - Landing Page Management
        - Campaign Creation and Execution
        - Real-time Email Tracking
        - Comprehensive Reporting
        - Billing and Subscription Management
        - Real-time Notifications

        ## Authentication
        This API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:
        ```
        Authorization: Bearer <your_access_token>
        ```

        ## Rate Limiting
        API requests are rate-limited to prevent abuse. Current limits:
        - 1000 requests per hour for authenticated users
        - 100 requests per hour for unauthenticated requests

        ## Pagination
        List endpoints support pagination with the following query parameters:
        - `page`: Page number (default: 1)
        - `page_size`: Number of items per page (default: 25, max: 100)

        ## Filtering and Search
        Most list endpoints support filtering and search:
        - Use query parameters for filtering (e.g., `?status=active`)
        - Use `search` parameter for text search
        - Use `ordering` parameter for sorting (e.g., `?ordering=-created_at`)
        """,
        terms_of_service="https://www.yourcompany.com/terms/",
        contact=openapi.Contact(
            name="API Support",
            email="support@yourcompany.com",
            url="https://www.yourcompany.com/support/",
        ),
        license=openapi.License(
            name="MIT License", url="https://opensource.org/licenses/MIT"
        ),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[JWTAuthentication],
    patterns=[
        path("api/v1/", include("phishing_mvp_backend.api_urls")),
    ],
)


def api_health_check(request):
    """API Health check endpoint"""
    return JsonResponse(
        {
            "status": "healthy",
            "timestamp": timezone.now().isoformat(),
            "version": "1.0.0",
            "environment": settings.DEBUG and "development" or "production",
        }
    )


def api_info(request):
    """API Information endpoint"""
    return JsonResponse(
        {
            "name": "Phishing Simulation API",
            "version": "1.0.0",
            "description": "Comprehensive phishing simulation platform API",
            "docs_url": "/api/docs/",
            "redoc_url": "/api/redoc/",
            "schema_url": "/api/schema/",
            "endpoints": {
                "authentication": "/api/v1/auth/",
                "users": "/api/v1/users/",
                "targets": "/api/v1/targets/",
                "campaigns": "/api/v1/campaigns/",
                "emails": "/api/v1/emails/",
                "reports": "/api/v1/reports/",
                "notifications": "/api/v1/notifications/",
                "billing": "/api/v1/billing/",
            },
        }
    )


urlpatterns = [
    # Admin interface
    path("admin/", admin.site.urls),
    # API documentation
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "swagger/redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
    re_path(
        r"^api/swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    # API health and info
    path("api/health/", api_health_check, name="api-health"),
    path("api/", api_info, name="api-info"),
    # JWT authentication endpoints
    path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path(
        "api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"
    ),
    path("api/v1/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # API v1 endpoints
    path("api/v1/", include("phishing_mvp_backend.api_urls")),
]
