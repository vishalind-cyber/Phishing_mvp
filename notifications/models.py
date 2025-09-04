from django.db import models
from django.utils import timezone
from users.models import CustomUser, Organization
from campaigns.models import Campaign
from targets.models import Target
import uuid


class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('campaign_started', 'Campaign Started'),
        ('campaign_completed', 'Campaign Completed'),
        ('high_risk_click', 'High Risk Click Detected'),
        ('security_breach', 'Potential Security Breach'),
        ('report_ready', 'Report Ready'),
        ('system_alert', 'System Alert'),
        ('billing_alert', 'Billing Alert'),
        ('training_reminder', 'Training Reminder')
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')

    title = models.CharField(max_length=255)
    message = models.TextField()

    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')

    is_read = models.BooleanField(default=False)
    is_email_sent = models.BooleanField(default=False)

    # Related objects
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    target = models.ForeignKey(Target, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')

    action_url = models.URLField(blank=True)
    action_label = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} -> {self.recipient.username}"

    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save()


class NotificationPreference(models.Model):
    DIGEST_FREQUENCY_CHOICES = [
        ('realtime', 'Real-time'),
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Digest'),
        ('disabled', 'Disabled')
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='notification_preferences')

    # Email notifications
    email_campaign_updates = models.BooleanField(default=True)
    email_security_alerts = models.BooleanField(default=True)
    email_reports = models.BooleanField(default=True)
    email_billing = models.BooleanField(default=True)

    # In-app notifications
    app_campaign_updates = models.BooleanField(default=True)
    app_security_alerts = models.BooleanField(default=True)
    app_system_alerts = models.BooleanField(default=True)

    # Frequency settings
    digest_frequency = models.CharField(max_length=20, choices=DIGEST_FREQUENCY_CHOICES, default='realtime')

    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_preferences'

    def __str__(self):
        return f"Preferences: {self.user.username}"


class AlertRule(models.Model):
    TRIGGER_TYPE_CHOICES = [
        ('click_rate_threshold', 'Click Rate Threshold'),
        ('multiple_clicks_same_ip', 'Multiple Clicks Same IP'),
        ('credential_submission', 'Credential Submission'),
        ('campaign_completion', 'Campaign Completion'),
        ('failed_email_threshold', 'Failed Email Threshold'),
        ('high_risk_user_click', 'High Risk User Click')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='alert_rules')
    name = models.CharField(max_length=255)

    trigger_type = models.CharField(max_length=50, choices=TRIGGER_TYPE_CHOICES)
    threshold_value = models.FloatField(null=True, blank=True)
    time_window_minutes = models.IntegerField(default=60)

    is_active = models.BooleanField(default=True)
    notify_users = models.ManyToManyField(CustomUser, related_name='alert_rules')

    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_alert_rules')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'alert_rules'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_trigger_type_display()})"