# permissions.py - Custom permission classes

from django.contrib.auth.models import AnonymousUser
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `created_by` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `created_by`.
        return obj.created_by == request.user


class IsOrganizationMember(permissions.BasePermission):
    """
    Permission to check if user belongs to the same organization as the object.
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False
        return request.user.is_authenticated and hasattr(request.user, 'organization')

    def has_object_permission(self, request, view, obj):
        if isinstance(request.user, AnonymousUser):
            return False

        # Check if object has organization attribute
        if hasattr(obj, 'organization'):
            return obj.organization == request.user.organization

        # For objects related to user (like UserProfile)
        if hasattr(obj, 'user') and hasattr(obj.user, 'organization'):
            return obj.user.organization == request.user.organization

        return False


class IsOrganizationAdmin(permissions.BasePermission):
    """
    Permission to check if user is an admin of their organization.
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'organization') and
            request.user.role in ['admin', 'customer']
        )


class IsPlatformAdmin(permissions.BasePermission):
    """
    Permission for platform administrators only.
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False
        return (
            request.user.is_authenticated and
            request.user.role == 'admin' and
            request.user.is_staff
        )


class IsCustomerOrAdmin(permissions.BasePermission):
    """
    Permission for customers and admins, excluding targets.
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False
        return (
            request.user.is_authenticated and
            request.user.role in ['admin', 'customer']
        )


class IsTargetUser(permissions.BasePermission):
    """
    Permission specifically for target users.
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False
        return (
            request.user.is_authenticated and
            request.user.role == 'target'
        )


class CanManageCampaigns(permissions.BasePermission):
    """
    Permission for users who can manage campaigns.
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False
        return (
            request.user.is_authenticated and
            request.user.role in ['admin', 'customer'] and
            hasattr(request.user, 'organization')
        )

    def has_object_permission(self, request, view, obj):
        # Users can only manage campaigns in their organization
        if hasattr(obj, 'organization'):
            return obj.organization == request.user.organization
        return False


class CanViewReports(permissions.BasePermission):
    """
    Permission for users who can view reports.
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False
        return (
            request.user.is_authenticated and
            request.user.role in ['admin', 'customer']
        )

    def has_object_permission(self, request, view, obj):
        # Check organization access for reports
        if hasattr(obj, 'organization'):
            return obj.organization == request.user.organization
        if hasattr(obj, 'campaign') and hasattr(obj.campaign, 'organization'):
            return obj.campaign.organization == request.user.organization
        return False


class CanManageTargets(permissions.BasePermission):
    """
    Permission for users who can manage targets.
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False
        return (
            request.user.is_authenticated and
            request.user.role in ['admin', 'customer'] and
            hasattr(request.user, 'organization')
        )

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'organization'):
            return obj.organization == request.user.organization
        return False


class CanAccessBilling(permissions.BasePermission):
    """
    Permission for users who can access billing information.
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False
        return (
            request.user.is_authenticated and
            request.user.role in ['admin', 'customer'] and
            hasattr(request.user, 'organization')
        )

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'organization'):
            return obj.organization == request.user.organization
        return False


class ReadOnlyPermission(permissions.BasePermission):
    """
    Permission that allows only read operations.
    """

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsOwnerOrOrganizationAdmin(permissions.BasePermission):
    """
    Permission that allows access to owners or organization admins.
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(request.user, AnonymousUser):
            return False

        # Owner can always access
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True

        # Organization admin can access
        if (request.user.role in ['admin', 'customer'] and
            hasattr(obj, 'organization') and
                obj.organization == request.user.organization):
            return True

        return False


class CanManageEmailTemplates(permissions.BasePermission):
    """
    Permission for users who can manage email templates.
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False
        return (
            request.user.is_authenticated and
            request.user.role in ['admin', 'customer']
        )

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'organization'):
            return obj.organization == request.user.organization
        return False


class CanAccessNotifications(permissions.BasePermission):
    """
    Permission for accessing notifications.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Users can only access their own notifications
        if hasattr(obj, 'recipient'):
            return obj.recipient == request.user

        # Or notifications for their organization
        if hasattr(obj, 'organization'):
            return obj.organization == request.user.organization

        return False


# Utility functions for permission checking
def has_organization_access(user, obj):
    """
    Utility function to check if user has organization access to object.
    """
    if isinstance(user, AnonymousUser):
        return False

    if not hasattr(user, 'organization') or not user.organization:
        return False

    if hasattr(obj, 'organization'):
        return obj.organization == user.organization

    if hasattr(obj, 'user') and hasattr(obj.user, 'organization'):
        return obj.user.organization == user.organization

    if hasattr(obj, 'campaign') and hasattr(obj.campaign, 'organization'):
        return obj.campaign.organization == user.organization

    return False


def is_organization_admin(user):
    """
    Utility function to check if user is organization admin.
    """
    if isinstance(user, AnonymousUser):
        return False
    return (
        user.is_authenticated and
        user.role in ['admin', 'customer'] and
        hasattr(user, 'organization')
    )


def can_manage_resource(user, resource_type):
    """
    Utility function to check if user can manage specific resource type.
    """
    if isinstance(user, AnonymousUser):
        return False

    if user.role == 'admin':
        return True

    if user.role == 'customer':
        allowed_resources = [
            'campaigns', 'targets', 'templates', 'landing_pages',
            'notifications', 'reports'
        ]
        return resource_type in allowed_resources

    return False
