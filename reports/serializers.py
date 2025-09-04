from rest_framework import serializers

from campaigns.models import Campaign
from .tasks import generate_scheduled_report

from .models import CampaignReport, DepartmentReport, ScheduledReport


class CampaignReportSerializer(serializers.ModelSerializer):
    campaign_name = serializers.CharField(source="campaign.name", read_only=True)
    campaign_status = serializers.CharField(source="campaign.status", read_only=True)

    class Meta:
        model = CampaignReport
        fields = [
            "id",
            "campaign",
            "campaign_name",
            "campaign_status",
            "total_emails",
            "emails_sent",
            "emails_delivered",
            "emails_bounced",
            "emails_opened",
            "emails_clicked",
            "page_visits",
            "credentials_captured",
            "data_submitted",
            "emails_reported",
            "delivery_rate",
            "open_rate",
            "click_rate",
            "click_through_rate",
            "susceptibility_rate",
            "awareness_rate",
            "last_updated",
        ]
        read_only_fields = ["id", "last_updated"]


class DepartmentReportSerializer(serializers.ModelSerializer):
    campaign_name = serializers.CharField(source="campaign.name", read_only=True)

    class Meta:
        model = DepartmentReport
        fields = [
            "id",
            "campaign",
            "campaign_name",
            "department",
            "total_employees",
            "emails_sent",
            "emails_opened",
            "links_clicked",
            "data_submitted",
            "emails_reported",
            "risk_score",
            "improvement_percentage",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ScheduledReportSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )
    campaigns = serializers.StringRelatedField(
        source="include_campaigns", many=True, read_only=True
    )
    campaign_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Campaign.objects.none(),
        required=False,
        source="include_campaigns",
    )

    class Meta:
        model = ScheduledReport
        fields = [
            "id",
            "name",
            "report_type",
            "frequency",
            "recipients",
            "campaigns",
            "campaign_ids",
            "next_run",
            "last_run",
            "is_active",
            "created_by",
            "created_by_name",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "created_by", "last_run"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and hasattr(request.user, "organization"):
            self.fields["campaign_ids"].queryset = Campaign.objects.filter(
                organization=request.user.organization
            )

    def create(self, validated_data):
        validated_data["organization"] = self.context["request"].user.organization
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

        generate_scheduled_report.delay(str(report.id))
