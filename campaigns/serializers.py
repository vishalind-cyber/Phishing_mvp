from django.utils import timezone
from rest_framework import serializers

from notifications.models import Notification
from notifications.tasks import send_notification
from targets.models import Target, TargetGroup
from users.serializers import CustomUserSerializer

from .models import Campaign, CampaignTarget, EmailTemplate, LandingPage
from .tasks import process_campaign_emails


class EmailTemplateSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )
    campaigns_count = serializers.SerializerMethodField()

    class Meta:
        model = EmailTemplate
        fields = [
            "id",
            "name",
            "subject",
            "sender_name",
            "sender_email",
            "html_content",
            "text_content",
            "template_type",
            "difficulty_level",
            "is_default",
            "created_by",
            "created_by_name",
            "created_at",
            "campaigns_count",
        ]
        read_only_fields = ["id", "created_at", "created_by", "campaigns_count"]

    def get_campaigns_count(self, obj):
        return obj.campaigns.count()

    def create(self, validated_data):
        validated_data["organization"] = self.context["request"].user.organization
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class LandingPageSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )
    campaigns_count = serializers.SerializerMethodField()

    class Meta:
        model = LandingPage
        fields = [
            "id",
            "name",
            "html_content",
            "css_content",
            "redirect_url",
            "page_type",
            "capture_credentials",
            "capture_form_data",
            "show_awareness_message",
            "awareness_message",
            "created_by",
            "created_by_name",
            "created_at",
            "campaigns_count",
        ]
        read_only_fields = ["id", "created_at", "created_by", "campaigns_count"]

    def get_campaigns_count(self, obj):
        return obj.campaigns.count()

    def create(self, validated_data):
        validated_data["organization"] = self.context["request"].user.organization
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class CampaignTargetSerializer(serializers.ModelSerializer):
    target_name = serializers.CharField(source="target.full_name", read_only=True)
    target_email = serializers.CharField(source="target.email", read_only=True)
    target_department = serializers.CharField(
        source="target.department", read_only=True
    )

    class Meta:
        model = CampaignTarget
        fields = [
            "id",
            "target",
            "target_name",
            "target_email",
            "target_department",
            "status",
            "email_sent_at",
            "email_opened_at",
            "link_clicked_at",
            "data_submitted_at",
            "reported_at",
            "ip_address",
            "user_agent",
            "submitted_data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "target_name",
            "target_email",
            "target_department",
        ]


class CampaignSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="template.name", read_only=True)
    landing_page_name = serializers.CharField(
        source="landing_page.name", read_only=True
    )
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )

    # Write-only fields for creating/updating
    target_group_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=TargetGroup.objects.none(), required=False
    )
    individual_target_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Target.objects.none(), required=False
    )

    # Read-only fields for display
    target_groups = serializers.StringRelatedField(many=True, read_only=True)
    individual_targets = serializers.StringRelatedField(many=True, read_only=True)

    # Campaign statistics
    total_targets = serializers.SerializerMethodField()
    emails_sent = serializers.SerializerMethodField()
    emails_opened = serializers.SerializerMethodField()
    links_clicked = serializers.SerializerMethodField()
    data_submitted = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            "id",
            "name",
            "description",
            "template",
            "template_name",
            "landing_page",
            "landing_page_name",
            "target_groups",
            "individual_targets",
            "target_group_ids",
            "individual_target_ids",
            "status",
            "scheduled_start",
            "actual_start",
            "end_date",
            "send_interval_minutes",
            "track_opens",
            "track_clicks",
            "capture_credentials",
            "capture_data",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
            "total_targets",
            "emails_sent",
            "emails_opened",
            "links_clicked",
            "data_submitted",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "actual_start",
            "end_date",
            "total_targets",
            "emails_sent",
            "emails_opened",
            "links_clicked",
            "data_submitted",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and hasattr(request.user, "organization"):
            org = request.user.organization
            self.fields["template"].queryset = EmailTemplate.objects.filter(
                organization=org
            )
            self.fields["landing_page"].queryset = LandingPage.objects.filter(
                organization=org
            )
            self.fields["target_group_ids"].queryset = TargetGroup.objects.filter(
                organization=org
            )
            self.fields["individual_target_ids"].queryset = Target.objects.filter(
                organization=org
            )

    def get_total_targets(self, obj):
        return obj.campaign_targets.count()

    def get_emails_sent(self, obj):
        return obj.campaign_targets.exclude(email_sent_at__isnull=True).count()

    def get_emails_opened(self, obj):
        return obj.campaign_targets.exclude(email_opened_at__isnull=True).count()

    def get_links_clicked(self, obj):
        return obj.campaign_targets.exclude(link_clicked_at__isnull=True).count()

    def get_data_submitted(self, obj):
        return obj.campaign_targets.exclude(data_submitted_at__isnull=True).count()

    def validate_scheduled_start(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError(
                "Scheduled start time must be in the future"
            )
        return value

    def create(self, validated_data):
        target_group_ids = validated_data.pop("target_group_ids", [])
        individual_target_ids = validated_data.pop("individual_target_ids", [])

        validated_data["organization"] = self.context["request"].user.organization
        validated_data["created_by"] = self.context["request"].user

        campaign = Campaign.objects.create(**validated_data)

        # Set target groups and individual targets
        campaign.target_groups.set(target_group_ids)
        campaign.individual_targets.set(individual_target_ids)

        # Create campaign targets
        self._create_campaign_targets(campaign)

        return campaign

    def update(self, instance, validated_data):
        target_group_ids = validated_data.pop("target_group_ids", None)
        individual_target_ids = validated_data.pop("individual_target_ids", None)
        prev_status = instance.status

        instance = super().update(instance, validated_data)

        if prev_status != "running" and instance.status == "running":
            process_campaign_emails.delay(str(instance.id))

            for user in instance.organization.users.filter(
                role__in=["admin", "customer"]
            ):
                notif = Notification.objects.create(
                    recipient=user,
                    campaign=instance,
                    title="Campaign Started",
                    message=f"The campaign '{instance.name}' has started.",
                    notification_type="campaign",
                    priority="info",
                )
                send_notification.delay(str(notif.id))

        if target_group_ids is not None or individual_target_ids is not None:
            if target_group_ids is not None:
                instance.target_groups.set(target_group_ids)
            if individual_target_ids is not None:
                instance.individual_targets.set(individual_target_ids)

            # Recreate campaign targets if campaign is still in draft
            if instance.status == "draft":
                instance.campaign_targets.all().delete()
                self._create_campaign_targets(instance)

        return instance

    def _create_campaign_targets(self, campaign):
        """Create CampaignTarget objects for all targets in the campaign"""
        all_targets = set()

        # Add targets from groups
        for group in campaign.target_groups.all():
            all_targets.update(group.targets.all())

        # Add individual targets
        all_targets.update(campaign.individual_targets.all())

        # Create campaign target records
        campaign_targets = []
        for target in all_targets:
            campaign_targets.append(CampaignTarget(campaign=campaign, target=target))

        CampaignTarget.objects.bulk_create(campaign_targets, ignore_conflicts=True)


class CampaignCreateSerializer(serializers.ModelSerializer):
    target_group_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True
    )
    individual_target_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True
    )

    class Meta:
        model = Campaign
        fields = [
            "name",
            "description",
            "template",
            "landing_page",
            "target_group_ids",
            "individual_target_ids",
            "scheduled_start",
            "send_interval_minutes",
            "track_opens",
            "track_clicks",
            "capture_credentials",
            "capture_data",
        ]

    def validate_target_group_ids(self, value):
        if not value:
            return []

        request = self.context.get("request")
        if not request or not hasattr(request.user, "organization"):
            raise serializers.ValidationError("User organization not found.")

        org = request.user.organization
        valid_ids = list(
            TargetGroup.objects.filter(id__in=value, organization=org).values_list(
                "id", flat=True
            )
        )

        invalid_ids = set(value) - set(valid_ids)
        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid target group IDs: {list(invalid_ids)}"
            )

        return TargetGroup.objects.filter(id__in=valid_ids)

    def validate_individual_target_ids(self, value):
        if not value:
            return []

        request = self.context.get("request")
        if not request or not hasattr(request.user, "organization"):
            raise serializers.ValidationError("User organization not found.")

        org = request.user.organization
        valid_ids = list(
            Target.objects.filter(id__in=value, organization=org).values_list(
                "id", flat=True
            )
        )

        invalid_ids = set(value) - set(valid_ids)
        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid target IDs: {list(invalid_ids)}"
            )

        return Target.objects.filter(id__in=valid_ids)

    def create(self, validated_data):
        # Pop M2M objects (now they're QuerySets, not IDs)
        target_groups = validated_data.pop("target_group_ids", [])
        individual_targets = validated_data.pop("individual_target_ids", [])

        # Create campaign
        campaign = Campaign.objects.create(
            **validated_data,
            created_by=self.context["request"].user,
            organization=self.context["request"].user.organization,
        )

        # Assign M2M relationships
        if target_groups:
            campaign.target_groups.set(target_groups)
            for group in target_groups:
                for target in group.targets.all():
                    CampaignTarget.objects.get_or_create(
                        campaign=campaign, target=target, defaults={"status": "pending"}
                    )

        if individual_targets:
            campaign.individual_targets.set(individual_targets)
            for target in individual_targets:
                CampaignTarget.objects.get_or_create(
                    campaign=campaign, target=target, defaults={"status": "pending"}
                )

        return campaign
