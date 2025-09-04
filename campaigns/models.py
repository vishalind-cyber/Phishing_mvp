from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import Organization, CustomUser
from targets.models import Target, TargetGroup
import uuid


class EmailTemplate(models.Model):
    TEMPLATE_TYPE_CHOICES = [
        ('social_media', 'Social Media'),
        ('it_support', 'IT Support'),
        ('hr_notice', 'HR Notice'),
        ('security_alert', 'Security Alert'),
        ('invoice', 'Invoice/Payment'),
        ('shipping', 'Shipping Notification'),
        ('banking', 'Banking Alert'),
        ('custom', 'Custom')
    ]

    DIFFICULTY_LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='email_templates')
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    sender_name = models.CharField(max_length=100)
    sender_email = models.EmailField()
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPE_CHOICES)
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVEL_CHOICES)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='email_templates')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'email_templates'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class LandingPage(models.Model):
    PAGE_TYPE_CHOICES = [
        ('login', 'Login Page'),
        ('survey', 'Survey Form'),
        ('download', 'File Download'),
        ('notification', 'Notification Page'),
        ('banking', 'Banking Portal'),
        ('social', 'Social Media'),
        ('custom', 'Custom Page')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='landing_pages')
    name = models.CharField(max_length=255)
    html_content = models.TextField()
    css_content = models.TextField(blank=True)
    redirect_url = models.URLField(blank=True)
    page_type = models.CharField(max_length=50, choices=PAGE_TYPE_CHOICES)
    capture_credentials = models.BooleanField(default=True)
    capture_form_data = models.BooleanField(default=True)
    show_awareness_message = models.BooleanField(default=True)
    awareness_message = models.TextField(blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='landing_pages')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'landing_pages'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_page_type_display()})"


class Campaign(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('running', 'Running'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='campaigns')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE, related_name='campaigns')
    landing_page = models.ForeignKey(LandingPage, on_delete=models.CASCADE, null=True, blank=True, related_name='campaigns')
    target_groups = models.ManyToManyField(TargetGroup, blank=True, related_name='campaigns')
    individual_targets = models.ManyToManyField(Target, blank=True, related_name='individual_campaigns')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_start = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    # Campaign settings
    send_interval_minutes = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(1440)]
    )  # 1 minute to 24 hours
    track_opens = models.BooleanField(default=True)
    track_clicks = models.BooleanField(default=True)
    capture_credentials = models.BooleanField(default=True)
    capture_data = models.BooleanField(default=True)

    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='campaigns')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campaigns'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class CampaignTarget(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Email Sent'),
        ('opened', 'Email Opened'),
        ('clicked', 'Link Clicked'),
        ('submitted', 'Data Submitted'),
        ('reported', 'Reported as Phishing'),
        ('failed', 'Failed to Send')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='campaign_targets')
    target = models.ForeignKey(Target, on_delete=models.CASCADE, related_name='campaign_participations')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_opened_at = models.DateTimeField(null=True, blank=True)
    link_clicked_at = models.DateTimeField(null=True, blank=True)
    data_submitted_at = models.DateTimeField(null=True, blank=True)
    reported_at = models.DateTimeField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    submitted_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campaign_targets'
        unique_together = ['campaign', 'target']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.campaign.name} -> {self.target.full_name} ({self.get_status_display()})"