from celery import shared_task
from django.utils import timezone
from campaigns.models import CampaignTarget


@shared_task
def send_campaign_email(campaign_target_id):
    try:
        ct = CampaignTarget.objects.get(id=campaign_target_id)
        # TODO: integrate real email service (SES, SendGrid, SMTP, etc.)
        print(f"Sending phishing email to {ct.target.email}")
        ct.status = "sent"
        ct.email_sent_at = timezone.now()
        ct.save()
    except CampaignTarget.DoesNotExist:
        print(f"CampaignTarget {campaign_target_id} not found")
