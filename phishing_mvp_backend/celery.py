# phishing_simulation/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "phishing_mvp_backend.settings")

app = Celery("phishing_mvp_backend")

# Load settings from Django, using CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks in all installed apps
app.autodiscover_tasks()
