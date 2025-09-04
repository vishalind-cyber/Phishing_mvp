from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.db.models import Count
from django.urls import path
from django.shortcuts import render
from django.utils import timezone


class PhishingSimAdminSite(AdminSite):
    site_header = 'Phishing Simulation Platform'
    site_title = 'Phishing Sim Admin'
    index_title = 'Dashboard'

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}

        # Get statistics for dashboard
        from users.models import Organization, CustomUser
        from campaigns.models import Campaign
        from targets.models import Target

        extra_context.update({
            'total_organizations': Organization.objects.count(),
            'total_users': CustomUser.objects.count(),
            'active_campaigns': Campaign.objects.filter(status='running').count(),
            'total_targets': Target.objects.count(),
        })

        return super().index(request, extra_context)


# Create custom admin site instance
admin_site = PhishingSimAdminSite(name='phishing_admin')

# Register all models with custom admin site
from users.admin import *
from targets.admin import *
from campaigns.admin import *
from emails.admin import *
from reports.admin import *
from notifications.admin import *
from billings.admin import *