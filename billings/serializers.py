from rest_framework import serializers

from .models import Invoice, PaymentMethod, Subscription, UsageMetric


class SubscriptionSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )

    class Meta:
        model = Subscription
        fields = [
            "id",
            "organization",
            "organization_name",
            "plan_name",
            "plan_type",
            "max_targets",
            "max_campaigns_per_month",
            "max_emails_per_month",
            "max_templates",
            "max_landing_pages",
            "advanced_reporting",
            "api_access",
            "custom_branding",
            "priority_support",
            "monthly_price",
            "annual_price",
            "billing_cycle",
            "status",
            "trial_end_date",
            "current_period_start",
            "current_period_end",
            "next_billing_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]


class InvoiceSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    subscription_plan = serializers.CharField(
        source="subscription.plan_name", read_only=True
    )

    class Meta:
        model = Invoice
        fields = [
            "id",
            "organization",
            "organization_name",
            "subscription",
            "subscription_plan",
            "invoice_number",
            "subtotal",
            "tax_amount",
            "discount_amount",
            "total_amount",
            "issue_date",
            "due_date",
            "paid_date",
            "status",
            "payment_method",
            "transaction_id",
            "period_start",
            "period_end",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "issue_date"]


class UsageMetricSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    usage_percentage = serializers.SerializerMethodField()

    class Meta:
        model = UsageMetric
        fields = [
            "id",
            "organization",
            "organization_name",
            "metric_type",
            "current_value",
            "limit_value",
            "usage_percentage",
            "measurement_date",
            "reset_date",
            "warning_threshold",
            "warning_sent",
            "limit_exceeded",
        ]
        read_only_fields = ["id", "organization", "measurement_date"]

    def get_usage_percentage(self, obj):
        if obj.limit_value > 0:
            return round((obj.current_value / obj.limit_value) * 100, 2)
        return 0


class PaymentMethodSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )

    class Meta:
        model = PaymentMethod
        fields = [
            "id",
            "organization",
            "organization_name",
            "method_type",
            "card_last_four",
            "card_brand",
            "expiry_month",
            "expiry_year",
            "is_default",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]
        extra_kwargs = {
            "stripe_payment_method_id": {"write_only": True},
            "paypal_payment_id": {"write_only": True},
        }
