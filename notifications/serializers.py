from rest_framework import serializers

from users.models import CustomUser

from .models import AlertRule, Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    campaign_name = serializers.CharField(source="campaign.name", read_only=True)
    target_name = serializers.CharField(source="target.full_name", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "message",
            "notification_type",
            "priority",
            "is_read",
            "is_email_sent",
            "campaign",
            "campaign_name",
            "target",
            "target_name",
            "action_url",
            "action_label",
            "created_at",
            "read_at",
            "expires_at",
        ]
        read_only_fields = ["id", "created_at", "read_at", "is_email_sent"]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "email_campaign_updates",
            "email_security_alerts",
            "email_reports",
            "email_billing",
            "app_campaign_updates",
            "app_security_alerts",
            "app_system_alerts",
            "digest_frequency",
            "quiet_hours_start",
            "quiet_hours_end",
            "timezone",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class AlertRuleSerializer(serializers.ModelSerializer):
    notify_users_names = serializers.SerializerMethodField()
    notify_user_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=CustomUser.objects.none(),
        source="notify_users",
        required=False,
    )
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )

    class Meta:
        model = AlertRule
        fields = [
            "id",
            "name",
            "trigger_type",
            "threshold_value",
            "time_window_minutes",
            "is_active",
            "notify_users",
            "notify_users_names",
            "notify_user_ids",
            "created_by",
            "created_by_name",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "created_by"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and hasattr(request.user, "organization"):
            self.fields["notify_user_ids"].queryset = CustomUser.objects.filter(
                organization=request.user.organization
            )

    def get_notify_users_names(self, obj):
        return [user.get_full_name() for user in obj.notify_users.all()]

    def create(self, validated_data):
        validated_data["organization"] = self.context["request"].user.organization
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
