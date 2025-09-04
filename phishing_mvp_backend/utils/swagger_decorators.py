# Create a utils/swagger_decorators.py file

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

# JWT Bearer token parameter for Swagger documentation
jwt_bearer_parameter = openapi.Parameter(
    'Authorization',
    openapi.IN_HEADER,
    description="JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'",
    type=openapi.TYPE_STRING,
    required=True,
    default='Bearer '
)

# Custom decorator for JWT authenticated endpoints


def swagger_jwt_auth(operation_description="", **kwargs):
    """
    Decorator to add JWT authentication documentation to Swagger
    """
    return swagger_auto_schema(
        operation_description=operation_description,
        manual_parameters=[jwt_bearer_parameter],
        security=[{'Bearer': []}],
        **kwargs
    )


# Responses for common JWT authentication errors
jwt_auth_responses = {
    401: openapi.Response(
        description="Unauthorized - Invalid or missing JWT token",
        examples={
            "application/json": {
                "detail": "Given token not valid for any token type",
                "code": "token_not_valid",
                "messages": [
                    {
                        "token_class": "AccessToken",
                        "token_type": "access",
                        "message": "Token is invalid or expired"
                    }
                ]
            }
        }
    ),
    403: openapi.Response(
        description="Forbidden - Insufficient permissions",
        examples={
            "application/json": {
                "detail": "You do not have permission to perform this action."
            }
        }
    )
}

# Usage example in your views:
"""
from utils.swagger_decorators import swagger_jwt_auth, jwt_auth_responses

class UserListView(generics.ListCreateAPIView):
    # ... your view code ...

    @swagger_jwt_auth(
        operation_description="Get list of users in organization",
        responses={
            200: CustomUserSerializer(many=True),
            **jwt_auth_responses
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_jwt_auth(
        operation_description="Create a new user",
        request_body=CreateUserSerializer,
        responses={
            201: CustomUserSerializer,
            400: "Validation errors",
            **jwt_auth_responses
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
"""
