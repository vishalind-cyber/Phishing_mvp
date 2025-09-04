from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import CustomUser, Organization, UserProfile


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating organizations during user registration"""

    class Meta:
        model = Organization
        fields = ["name", "domain", "industry", "size"]

    def validate_domain(self, value):
        """Ensure domain is unique"""
        if Organization.objects.filter(domain=value).exists():
            raise serializers.ValidationError(
                "An organization with this domain already exists."
            )
        return value


class OrganizationSerializer(serializers.ModelSerializer):
    users_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "domain",
            "industry",
            "size",
            "subscription_tier",
            "created_at",
            "is_active",
            "users_count",
        ]
        read_only_fields = ["id", "created_at", "users_count"]

    def get_users_count(self, obj):
        return obj.users.count()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["department", "job_title", "security_level", "last_training_date"]


class CustomUserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "organization",
            "organization_name",
            "phone",
            "is_verified",
            "is_active",
            "created_at",
            "updated_at",
            "profile",
            "full_name",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {"password": {"write_only": True}}


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    profile_data = UserProfileSerializer(required=False)
    organization_data = OrganizationCreateSerializer(required=False)
    organization_id = serializers.UUIDField(
        required=False, help_text="Existing organization ID"
    )

    class Meta:
        model = CustomUser
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "organization_id",
            "organization_data",
            "phone",
            "password",
            "password_confirm",
            "profile_data",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Passwords don't match")

        organization_data = attrs.get("organization_data")
        organization_id = attrs.get("organization_id")
        role = attrs.get("role", "customer")

        if role == "customer":
            # Customer users must either create a new org or join an existing one
            if not organization_data and not organization_id:
                raise serializers.ValidationError(
                    "Customer users must either provide organization_data to create a new organization "
                    "or organization_id to join an existing organization."
                )

            if organization_data and organization_id:
                raise serializers.ValidationError(
                    "Provide either organization_data (to create new) or organization_id (to join existing), not both."
                )

        elif role == "target":
            # Target users must join an existing organization
            if not organization_id:
                raise serializers.ValidationError(
                    "Target users must provide organization_id to join an existing organization."
                )

            if organization_data:
                raise serializers.ValidationError(
                    "Target users cannot create new organizations."
                )

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        profile_data = validated_data.pop("profile_data", {})
        organization_data = validated_data.pop("organization_data", None)
        organization_id = validated_data.pop("organization_id", None)
        password = validated_data.pop("password")

        # Handle organization creation or assignment
        organization = None

        if organization_data:
            # Create new organization
            org_serializer = OrganizationCreateSerializer(data=organization_data)
            if org_serializer.is_valid():
                organization = org_serializer.save()
            else:
                raise serializers.ValidationError(
                    {"organization_data": org_serializer.errors}
                )

        elif organization_id:
            # Join existing organization
            try:
                organization = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                raise serializers.ValidationError(
                    {"organization_id": "Organization not found."}
                )

        # Create user with organization
        validated_data["organization"] = organization

        user = CustomUser.objects.create_user(password=password, **validated_data)

        if profile_data:
            UserProfile.objects.create(user=user, **profile_data)

        return user


class CreateUserWithOrganizationResponseSerializer(serializers.ModelSerializer):
    """Response serializer that includes organization details"""

    profile = UserProfileSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "organization",
            "phone",
            "is_verified",
            "is_active",
            "created_at",
            "profile",
            "full_name",
        ]


class UpdateUserSerializer(serializers.ModelSerializer):
    profile_data = UserProfileSerializer(required=False)

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "phone", "profile_data"]

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile_data", {})

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update profile
        if profile_data:
            profile, created = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("New passwords don't match")
        if attrs["new_password"] == attrs["old_password"]:
            raise serializers.ValidationError(
                "New Password must not be same as Old Password"
            )
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(
                request=self.context.get("request"), email=email, password=password
            )

            if not user:
                raise serializers.ValidationError("Invalid email or password")

            if not user.is_active:
                raise serializers.ValidationError("User account is disabled")

            attrs["user"] = user
            return attrs

        raise serializers.ValidationError("Must include email and password")
