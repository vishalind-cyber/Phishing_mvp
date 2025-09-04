from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from campaigns.models import Campaign
from users.models import Organization, CustomUser
import uuid


class CampaignReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.OneToOneField(Campaign, on_delete=models.CASCADE, related_name='report')

    # Email Statistics
    total_emails = models.IntegerField(default=0)
    emails_sent = models.IntegerField(default=0)
    emails_delivered = models.IntegerField(default=0)
    emails_bounced = models.IntegerField(default=0)
    emails_opened = models.IntegerField(default=0)
    emails_clicked = models.IntegerField(default=0)

    # Landing Page Statistics
    page_visits = models.IntegerField(default=0)
    credentials_captured = models.IntegerField(default=0)
    data_submitted = models.IntegerField(default=0)

    # Security Awareness
    emails_reported = models.IntegerField(default=0)

    # Calculated Metrics (0-100 percentage)
    delivery_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    open_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    click_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    click_through_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )  # Clicks/Opens
    susceptibility_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )  # Data submitted/Delivered
    awareness_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )  # Reported/Delivered

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campaign_reports'

    def __str__(self):
        return f"Report: {self.campaign.name}"


class DepartmentReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='department_reports')
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='department_reports')
    department = models.CharField(max_length=100)

    total_employees = models.IntegerField()
    emails_sent = models.IntegerField(default=0)
    emails_opened = models.IntegerField(default=0)
    links_clicked = models.IntegerField(default=0)
    data_submitted = models.IntegerField(default=0)
    emails_reported = models.IntegerField(default=0)

    # Risk Assessment
    risk_score = models.FloatField(default=0.0)  # Calculated risk score 0-100
    improvement_percentage = models.FloatField(default=0.0)  # Compared to previous campaigns

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'department_reports'
        unique_together = ['campaign', 'department']
        ordering = ['department']

    def __str__(self):
        return f"{self.department} - {self.campaign.name}"


class ScheduledReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ('campaign_summary', 'Campaign Summary'),
        ('security_metrics', 'Security Metrics'),
        ('department_breakdown', 'Department Breakdown'),
        ('trend_analysis', 'Trend Analysis'),
        ('executive_summary', 'Executive Summary')
    ]

    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='scheduled_reports')
    name = models.CharField(max_length=255)

    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)

    recipients = models.JSONField(default=list)  # List of email addresses
    include_campaigns = models.ManyToManyField(Campaign, blank=True, related_name='scheduled_reports')

    next_run = models.DateTimeField()
    last_run = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='scheduled_reports')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'scheduled_reports'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"