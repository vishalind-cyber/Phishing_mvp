from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import EmailTemplate, LandingPage, Campaign, CampaignTarget


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'difficulty_level', 'sender_email', 'is_default', 'organization', 'created_by', 'created_at']
    list_filter = ['template_type', 'difficulty_level', 'is_default', 'organization', 'created_at']
    search_fields = ['name', 'subject', 'sender_name', 'sender_email']
    readonly_fields = ['id', 'created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'created_by')


@admin.register(LandingPage)
class LandingPageAdmin(admin.ModelAdmin):
    list_display = ['name', 'page_type', 'capture_credentials', 'capture_form_data', 'show_awareness_message', 'organization', 'created_by', 'created_at']
    list_filter = ['page_type', 'capture_credentials', 'capture_form_data', 'show_awareness_message', 'organization', 'created_at']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'created_by')


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'target_count', 'organization', 'scheduled_start', 'created_by', 'created_at']
    list_filter = ['status', 'organization', 'scheduled_start', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['target_groups', 'individual_targets']
    readonly_fields = ['id', 'created_at', 'updated_at', 'actual_start', 'end_date']
    date_hierarchy = 'created_at'

    def target_count(self, obj):
        return obj.campaign_targets.count()
    target_count.short_description = 'Targets'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'created_by', 'template', 'landing_page').prefetch_related('campaign_targets')


@admin.register(CampaignTarget)
class CampaignTargetAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'target', 'status', 'email_sent_at', 'email_opened_at', 'link_clicked_at', 'data_submitted_at']
    list_filter = ['status', 'campaign__organization', 'email_sent_at', 'created_at']
    search_fields = ['campaign__name', 'target__first_name', 'target__last_name', 'target__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('campaign', 'target', 'campaign__organization')