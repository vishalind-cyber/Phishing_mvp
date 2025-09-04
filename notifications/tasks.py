from celery import shared_task
from .models import Notification


@shared_task
def send_notification(notification_id):
    notif = Notification.objects.get(id=notification_id)
    # TODO: integrate with Slack/Email push
    print(f"Sending notification to {notif.recipient.email}: {notif.title}")
