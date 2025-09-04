from django.contrib import admin
from django.utils.html import format_html
from .models import CampaignReport, DepartmentReport, ScheduledReport


@admin.register(CampaignReport)
class CampaignReportAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'delivery_rate', 'open_rate', 'click_rate', 'susceptibility_rate', 'awareness_rate', 'last_updated']
    list_filter = ['campaign__organization', 'last_updated']
    search_fields = ['campaign__name']
    readonly_fields = ['id', 'last_updated']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('campaign', 'campaign__organization')


@admin.register(DepartmentReport)
class DepartmentReportAdmin(admin.ModelAdmin):
    list_display = ['department', 'campaign', 'total_employees', 'risk_score', 'improvement_percentage', 'created_at']
    list_filter = ['organization', 'department', 'created_at']
    search_fields = ['department', 'campaign__name']
    readonly_fields = ['id', 'created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'campaign')


@admin.register(ScheduledReport)
class ScheduledReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'frequency', 'is_active', 'next_run', 'last_run', 'organization']
    list_filter = ['report_type', 'frequency', 'is_active', 'organization']
    search_fields = ['name']
    filter_horizontal = ['include_campaigns']
    readonly_fields = ['id', 'created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'created_by')