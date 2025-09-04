from django.contrib import admin
from django.utils.html import format_html
from .models import Subscription, Invoice, UsageMetric, PaymentMethod


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['organization', 'plan_name', 'status', 'billing_cycle', 'monthly_price', 'current_period_end', 'next_billing_date']
    list_filter = ['plan_type', 'status', 'billing_cycle', 'advanced_reporting', 'api_access']
    search_fields = ['organization__name', 'plan_name']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'organization', 'status', 'total_amount', 'issue_date', 'due_date', 'paid_date']
    list_filter = ['status', 'issue_date', 'paid_date']
    search_fields = ['invoice_number', 'organization__name', 'transaction_id']
    readonly_fields = ['id', 'created_at', 'issue_date']
    date_hierarchy = 'issue_date'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'subscription')


@admin.register(UsageMetric)
class UsageMetricAdmin(admin.ModelAdmin):
    list_display = ['organization', 'metric_type', 'current_value', 'limit_value', 'usage_percentage', 'warning_sent', 'limit_exceeded']
    list_filter = ['metric_type', 'warning_sent', 'limit_exceeded', 'organization']
    search_fields = ['organization__name']
    readonly_fields = ['id', 'measurement_date']

    def usage_percentage(self, obj):
        if obj.limit_value > 0:
            percentage = (obj.current_value / obj.limit_value) * 100
            color = 'red' if percentage >= 100 else 'orange' if percentage >= 80 else 'green'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                color,
                percentage
            )
        return '0%'
    usage_percentage.short_description = 'Usage %'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization')


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['organization', 'method_type', 'masked_details', 'is_default', 'is_active', 'created_at']
    list_filter = ['method_type', 'is_default', 'is_active', 'card_brand']
    search_fields = ['organization__name', 'card_last_four']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def masked_details(self, obj):
        if obj.card_last_four:
            return f"{obj.card_brand} ****{obj.card_last_four}"
        return obj.get_method_type_display()
    masked_details.short_description = 'Payment Details'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization')