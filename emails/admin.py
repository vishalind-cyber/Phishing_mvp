from django.contrib import admin
from .models import SMTPConfiguration, EmailQueue, EmailEvent


@admin.register(SMTPConfiguration)
class SMTPConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'host', 'port', 'from_email', 'is_active', 'daily_limit', 'current_daily_count', 'organization']
    list_filter = ['is_active', 'use_tls', 'use_ssl', 'organization']
    search_fields = ['name', 'host', 'from_email']
    readonly_fields = ['id', 'created_at', 'current_daily_count', 'last_reset_date']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization')


@admin.register(EmailQueue)
class EmailQueueAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'target_email', 'status', 'scheduled_time', 'sent_time', 'retry_count']
    list_filter = ['status', 'campaign__organization', 'scheduled_time', 'created_at']
    search_fields = ['target__email', 'campaign__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'scheduled_time'

    def target_email(self, obj):
        return obj.target.email
    target_email.short_description = 'Target Email'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('campaign', 'target', 'campaign__organization')


@admin.register(EmailEvent)
class EmailEventAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'target_email', 'event_type', 'timestamp', 'ip_address', 'location']
    list_filter = ['event_type', 'campaign__organization', 'timestamp']
    search_fields = ['target__email', 'campaign__name', 'ip_address']
    readonly_fields = ['id', 'timestamp']
    date_hierarchy = 'timestamp'

    def target_email(self, obj):
        return obj.target.email
    target_email.short_description = 'Target Email'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('campaign', 'target', 'campaign__organization')