from celery import shared_task
from django.utils import timezone
from .models import Campaign, CampaignTarget
from emails.models import EmailQueue


@shared_task
def process_campaign_emails(campaign_id):
    """Process and queue emails for a campaign"""
    try:
        campaign = Campaign.objects.get(id=campaign_id)

        if campaign.status != "running":
            return f"Campaign {campaign_id} is not running"

        # Get pending campaign targets
        targets = CampaignTarget.objects.filter(
            campaign=campaign, status="pending"
        ).select_related("target")

        queued_count = 0
        for campaign_target in targets[:100]:  # Process in batches
            # Create email queue entry
            EmailQueue.objects.create(
                campaign=campaign,
                target=campaign_target.target,
                scheduled_time=timezone.now(),
            )

            # Update campaign target status
            campaign_target.status = "sent"
            campaign_target.email_sent_at = timezone.now()
            campaign_target.save()

            queued_count += 1

        return f"Queued {queued_count} emails for campaign {campaign.name}"

    except Campaign.DoesNotExist:
        return f"Campaign {campaign_id} not found"


@shared_task
def send_queued_emails():
    """Send queued emails"""
    from django.core.mail import send_mail
    from emails.models import EmailQueue

    # Get emails ready to send
    queued_emails = EmailQueue.objects.filter(
        status="queued", scheduled_time__lte=timezone.now()
    )[
        :50
    ]  # Process in batches

    sent_count = 0
    for email in queued_emails:
        try:
            # Send email using Django's email backend
            send_mail(
                subject=email.campaign.template.subject,
                message=email.campaign.template.text_content,
                from_email=email.campaign.template.sender_email,
                recipient_list=[email.target.email],
                html_message=email.campaign.template.html_content,
                fail_silently=False,
            )

            email.status = "sent"
            email.sent_time = timezone.now()
            email.save()

            sent_count += 1

        except Exception as e:
            email.status = "failed"
            email.error_message = str(e)
            email.retry_count += 1
            email.save()

    return f"Sent {sent_count} emails"
