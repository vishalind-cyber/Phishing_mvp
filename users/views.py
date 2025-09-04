from datetime import timedelta

from django.contrib.auth import login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser, Organization, UserProfile
from .permissions import (
    IsCustomerOrAdmin,
    IsOrganizationAdmin,
    IsOrganizationMember,
    IsPlatformAdmin,
)
from .serializers import (
    ChangePasswordSerializer,
    CreateUserSerializer,
    CreateUserWithOrganizationResponseSerializer,
    CustomUserSerializer,
    LoginSerializer,
    OrganizationCreateSerializer,
    OrganizationSerializer,
    UpdateUserSerializer,
    UserProfileSerializer,
)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "user": {
                            "id": "uuid",
                            "username": "john_doe",
                            "email": "john@example.com",
                        },
                    }
                },
            ),
            400: "Invalid credentials",
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": CustomUserSerializer(user).data,
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    @swagger_auto_schema(responses={200: "Logout successful"})
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        except Exception:
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    @swagger_auto_schema(responses={200: CustomUserSerializer})
    def get(self, request, *args, **kwargs):
        """Get current user profile"""
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=UpdateUserSerializer, responses={200: CustomUserSerializer}
    )
    def put(self, request, *args, **kwargs):
        """Update current user profile"""
        return super().put(request, *args, **kwargs)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        responses={200: "Password changed successfully"},
    )
    def put(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            user = request.user
            new_password = serializer.validated_data["new_password"]

            try:
                # 🔹 Validate password before setting it
                validate_password(new_password, user=user)
            except ValidationError as e:
                return Response(
                    {"new_password": list(e.messages)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.save()
            return Response({"message": "Password changed successfully"})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationListCreateView(generics.ListCreateAPIView):
    """
    GET: List all organizations (Platform admin only)
    POST: Create new organization (Anyone for customer self-signup, Platform admin for others)
    """

    serializer_class = OrganizationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["industry", "size", "subscription_tier", "is_active"]
    search_fields = ["name", "domain"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.role == "admin":
                return Organization.objects.all()
            if self.request.user.role == "customer":
                # Return only the user's organization
                return Organization.objects.filter(id=self.request.user.organization.id)
        return Organization.objects.none()

    def get_permissions(self):
        """
        GET: Platform admin only
        POST: Allow anyone (for customer self-signup) or platform admin
        """
        if self.request.method == "GET":
            return [IsCustomerOrAdmin()]
        elif self.request.method == "POST":
            return [permissions.AllowAny()]  # Allow organization creation during signup
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrganizationCreateSerializer
        return OrganizationSerializer

    @swagger_auto_schema(
        request_body=OrganizationCreateSerializer,
        responses={201: OrganizationSerializer},
    )
    def post(self, request, *args, **kwargs):
        """Create a new organization"""
        return super().post(request, *args, **kwargs)


class OrganizationDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = [IsOrganizationAdmin]

    def get_object(self):
        if self.request.user.role == "admin":
            return generics.get_object_or_404(Organization, pk=self.kwargs["pk"])
        return self.request.user.organization


class UserListView(generics.ListCreateAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [IsOrganizationAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["role", "is_active", "is_verified"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["username", "email", "created_at"]
    ordering = ["username"]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.role == "admin":
            return CustomUser.objects.all()
        elif self.request.user.is_authenticated:
            return CustomUser.objects.filter(
                organization=self.request.user.organization
            )
        return CustomUser.objects.none()

    def get_permissions(self):
        """
        Allow anyone to POST for self-signup,
        but restrict GET and admin creation.
        """
        if self.request.method == "POST":
            return []  # Anyone can attempt signup
        return [IsOrganizationAdmin()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateUserSerializer
        return CustomUserSerializer

    @swagger_auto_schema(
        request_body=CreateUserSerializer,
        responses={
            201: CreateUserWithOrganizationResponseSerializer,
            400: "Validation errors",
        },
        operation_description="""
        Create a new user account with optional organization creation.

        For customer users, you can either:
        1. Create a new organization by providing 'organization_data'
        2. Join an existing organization by providing 'organization_id'

        For target users:
        - Must provide 'organization_id' to join existing organization
        - Cannot create new organizations

        For admin users:
        - Only existing admins can create admin accounts
        """,
    )
    def post(self, request, *args, **kwargs):
        """Create a new user with optional organization creation"""
        serializer = CreateUserSerializer(data=request.data)

        if serializer.is_valid():
            role = serializer.validated_data.get("role", "customer")

            # Check admin creation permissions
            if role == "admin":
                if not request.user.is_authenticated or request.user.role != "admin":
                    raise PermissionDenied(
                        "Only platform admins can create admin accounts."
                    )

            user = serializer.save()

            # Return user data with organization details
            response_serializer = CreateUserWithOrganizationResponseSerializer(user)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [IsOrganizationAdmin]

    def get_queryset(self):
        if self.request.user.role == "admin":
            return CustomUser.objects.all()
        return CustomUser.objects.filter(organization=self.request.user.organization)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return UpdateUserSerializer
        return CustomUserSerializer


@swagger_auto_schema(
    method="get",
    responses={200: "User statistics"},
    manual_parameters=[
        openapi.Parameter(
            "organization",
            openapi.IN_QUERY,
            description="Organization ID",
            type=openapi.TYPE_STRING,
        )
    ],
)
@api_view(["GET"])
@permission_classes([IsCustomerOrAdmin])
def user_statistics(request):
    """Get user statistics for dashboard"""
    organization = request.user.organization

    if request.user.role == "admin" and request.GET.get("organization"):
        try:
            organization = Organization.objects.get(id=request.GET.get("organization"))
        except Organization.DoesNotExist:
            pass

    if not organization:
        return Response(
            {"error": "No organization found"}, status=status.HTTP_400_BAD_REQUEST
        )

    users_queryset = CustomUser.objects.filter(organization=organization)

    stats = {
        "total_users": users_queryset.count(),
        "active_users": users_queryset.filter(is_active=True).count(),
        "verified_users": users_queryset.filter(is_verified=True).count(),
        "users_by_role": {
            "admin": users_queryset.filter(role="admin").count(),
            "customer": users_queryset.filter(role="customer").count(),
            "target": users_queryset.filter(role="target").count(),
        },
        "recent_registrations": users_queryset.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count(),
    }

    return Response(stats)
