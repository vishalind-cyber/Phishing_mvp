# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import CustomUser, Organization, UserProfile


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'domain', 'industry', 'size',
                    'subscription_tier', 'is_active', 'created_at']
    list_filter = ['industry', 'size',
                   'subscription_tier', 'is_active', 'created_at']
    search_fields = ['name', 'domain']
    readonly_fields = ['id', 'created_at']
    list_per_page = 25

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ['email', 'username', 'get_full_name', 'role',
                    'organization', 'is_verified', 'is_active', 'date_joined']
    list_filter = ['role', 'is_verified',
                   'is_active', 'organization', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['email']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username',
         'first_name', 'last_name', 'phone')}),
        ('Organization', {'fields': ('role', 'organization', 'is_verified')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login',
         'date_joined', 'created_at', 'updated_at')}),
        ('UUID', {'fields': ('id',), 'classes': ('collapse',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'role', 'organization', 'password1', 'password2'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user_full_name', 'department',
                    'job_title', 'security_level', 'last_training_date']
    list_filter = ['security_level', 'department', 'last_training_date']
    search_fields = ['user__username',
                     'user__email', 'department', 'job_title']

    def user_full_name(self, obj):
        return obj.user.get_full_name()
    user_full_name.short_description = 'Full Name'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
