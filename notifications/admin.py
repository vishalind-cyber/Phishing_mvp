from django.contrib import admin
from django.utils.html import format_html
from .models import Notification, NotificationPreference, AlertRule


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient', 'notification_type', 'priority', 'is_read', 'created_at']
    list_filter = ['notification_type', 'priority', 'is_read', 'is_email_sent', 'created_at']
    search_fields = ['title', 'message', 'recipient__username']
    readonly_fields = ['id', 'created_at', 'read_at']
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient', 'campaign', 'target')


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'digest_frequency', 'email_security_alerts', 'app_security_alerts', 'timezone']
    list_filter = ['digest_frequency', 'email_security_alerts', 'app_security_alerts']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'trigger_type', 'threshold_value', 'time_window_minutes', 'is_active', 'organization']
    list_filter = ['trigger_type', 'is_active', 'organization']
    search_fields = ['name']
    filter_horizontal = ['notify_users']
    readonly_fields = ['id', 'created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'created_by')