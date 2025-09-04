from celery import shared_task
from .models import ScheduledReport
from django.utils import timezone
from notifications.models import Notification
from notifications.tasks import send_notification


@shared_task
def generate_scheduled_report(report_id):
    report = ScheduledReport.objects.get(id=report_id)
    # TODO: build report PDF/CSV and email it
    print(f"Generated report {report.name} for org {report.organization.name}")
    report.last_run = timezone.now()
    report.save()

    notif = Notification.objects.create(
        recipient=report.created_by,
        title="Scheduled Report Ready",
        message=f"Your scheduled report '{report.name}' is ready.",
        notification_type="report",
        priority="info",
    )
    send_notification.delay(str(notif.id))
