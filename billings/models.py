from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from users.models import Organization, CustomUser
import uuid


class Subscription(models.Model):
    PLAN_TYPE_CHOICES = [
        ('basic', 'Basic'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
        ('custom', 'Custom')
    ]

    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('annual', 'Annual')
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended'),
        ('trial', 'Trial')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='subscription')

    plan_name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES)

    # Limits
    max_targets = models.IntegerField()
    max_campaigns_per_month = models.IntegerField()
    max_emails_per_month = models.IntegerField()
    max_templates = models.IntegerField()
    max_landing_pages = models.IntegerField()

    # Features
    advanced_reporting = models.BooleanField(default=False)
    api_access = models.BooleanField(default=False)
    custom_branding = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)

    # Pricing
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    annual_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    trial_end_date = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    next_billing_date = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriptions'

    def __str__(self):
        return f"{self.organization.name} - {self.plan_name} ({self.get_status_display()})"


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='invoices')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='invoices')

    invoice_number = models.CharField(max_length=100, unique=True)

    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Dates
    issue_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    paid_date = models.DateTimeField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Payment info
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=255, blank=True)

    # Billing period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'invoices'
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.organization.name}"


class UsageMetric(models.Model):
    METRIC_TYPE_CHOICES = [
        ('targets_count', 'Active Targets'),
        ('campaigns_count', 'Campaigns This Month'),
        ('emails_sent', 'Emails Sent This Month'),
        ('storage_used', 'Storage Used (MB)'),
        ('api_requests', 'API Requests This Month')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='usage_metrics')

    metric_type = models.CharField(max_length=50, choices=METRIC_TYPE_CHOICES)
    current_value = models.IntegerField(default=0)
    limit_value = models.IntegerField()

    # Date tracking
    measurement_date = models.DateTimeField(auto_now=True)
    reset_date = models.DateTimeField()  # When the counter resets

    # Alerts
    warning_threshold = models.FloatField(default=0.8)  # 80% of limit
    warning_sent = models.BooleanField(default=False)
    limit_exceeded = models.BooleanField(default=False)

    class Meta:
        db_table = 'usage_metrics'
        unique_together = ['organization', 'metric_type']
        ordering = ['metric_type']

    def __str__(self):
        return f"{self.organization.name} - {self.get_metric_type_display()}: {self.current_value}/{self.limit_value}"


class PaymentMethod(models.Model):
    METHOD_TYPE_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='payment_methods')

    method_type = models.CharField(max_length=20, choices=METHOD_TYPE_CHOICES)

    # Encrypted payment details (store only references in production)
    card_last_four = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)
    expiry_month = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    expiry_year = models.IntegerField(null=True, blank=True)

    # External service IDs
    stripe_payment_method_id = models.CharField(max_length=255, blank=True)
    paypal_payment_id = models.CharField(max_length=255, blank=True)

    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_methods'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        if self.card_last_four:
            return f"{self.card_brand} ****{self.card_last_four}"
        return f"{self.get_method_type_display()}"