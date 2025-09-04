from django.contrib import admin
from django.utils.html import format_html
from .models import Target, TargetGroup, TargetTag, TargetImport


@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'department', 'job_title', 'risk_level', 'is_active', 'organization']
    list_filter = ['risk_level', 'is_active', 'department', 'organization', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'department', 'job_title']
    filter_horizontal = ['tags']
    readonly_fields = ['id', 'created_at']
    list_per_page = 50

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization').prefetch_related('tags')


@admin.register(TargetGroup)
class TargetGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'target_count', 'organization', 'created_by', 'created_at']
    list_filter = ['organization', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['targets']
    readonly_fields = ['id', 'created_at']

    def target_count(self, obj):
        return obj.targets.count()
    target_count.short_description = 'Targets Count'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'created_by')


@admin.register(TargetTag)
class TargetTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'colored_name', 'organization', 'target_count', 'created_at']
    list_filter = ['organization', 'created_at']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at']

    def colored_name(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            obj.color,
            obj.name
        )
    colored_name.short_description = 'Tag Preview'

    def target_count(self, obj):
        return obj.targets.count()
    target_count.short_description = 'Targets Count'


@admin.register(TargetImport)
class TargetImportAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'status', 'total_records', 'successful_imports', 'failed_imports', 'imported_by', 'created_at']
    list_filter = ['status', 'organization', 'created_at']
    search_fields = ['file_name']
    readonly_fields = ['id', 'created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'imported_by')