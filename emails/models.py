from django.db import models
from campaigns.models import Campaign
from targets.models import Target
from users.models import Organization
import uuid


class SMTPConfiguration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='smtp_configs')
    name = models.CharField(max_length=255)
    host = models.CharField(max_length=255)
    port = models.IntegerField()
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)  # Should be encrypted in production
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)


    from_email = models.EmailField()
    reply_to_email = models.EmailField(blank=True)

    is_active = models.BooleanField(default=True)
    daily_limit = models.IntegerField(default=1000)
    current_daily_count = models.IntegerField(default=0)
    last_reset_date = models.DateField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'smtp_configurations'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.host}:{self.port})"


class EmailQueue(models.Model):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='email_queue')
    target = models.ForeignKey(Target, on_delete=models.CASCADE, related_name='queued_emails')

    scheduled_time = models.DateTimeField()
    sent_time = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    retry_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'email_queue'
        ordering = ['scheduled_time']

    def __str__(self):
        return f"Email to {self.target.email} for {self.campaign.name} ({self.get_status_display()})"


class EmailEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ('sent', 'Email Sent'),
        ('delivered', 'Email Delivered'),
        ('bounced', 'Email Bounced'),
        ('opened', 'Email Opened'),
        ('clicked', 'Link Clicked'),
        ('reported', 'Reported as Spam/Phishing')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='email_events')
    target = models.ForeignKey(Target, on_delete=models.CASCADE, related_name='email_events')

    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)  # Geolocation

    # Email specific data
    message_id = models.CharField(max_length=255, blank=True)
    bounce_reason = models.CharField(max_length=255, blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'email_events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['campaign', 'event_type']),
            models.Index(fields=['target', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.target.email} ({self.timestamp})"