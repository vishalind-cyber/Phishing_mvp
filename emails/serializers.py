from rest_framework import serializers

from .models import EmailEvent, EmailQueue, SMTPConfiguration


class SMTPConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMTPConfiguration
        fields = [
            "id",
            "name",
            "host",
            "port",
            "username",
            "use_tls",
            "use_ssl",
            "from_email",
            "reply_to_email",
            "is_active",
            "daily_limit",
            "current_daily_count",
            "last_reset_date",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "current_daily_count",
            "last_reset_date",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        validated_data["organization"] = self.context["request"].user.organization
        return super().create(validated_data)


class EmailQueueSerializer(serializers.ModelSerializer):
    campaign_name = serializers.CharField(source="campaign.name", read_only=True)
    target_email = serializers.CharField(source="target.email", read_only=True)
    target_name = serializers.CharField(source="target.full_name", read_only=True)

    class Meta:
        model = EmailQueue
        fields = [
            "id",
            "campaign",
            "campaign_name",
            "target",
            "target_email",
            "target_name",
            "scheduled_time",
            "sent_time",
            "status",
            "retry_count",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EmailEventSerializer(serializers.ModelSerializer):
    campaign_name = serializers.CharField(source="campaign.name", read_only=True)
    target_email = serializers.CharField(source="target.email", read_only=True)
    target_name = serializers.CharField(source="target.full_name", read_only=True)

    class Meta:
        model = EmailEvent
        fields = [
            "id",
            "campaign",
            "campaign_name",
            "target",
            "target_email",
            "target_name",
            "event_type",
            "timestamp",
            "ip_address",
            "user_agent",
            "location",
            "message_id",
            "bounce_reason",
            "metadata",
        ]
        read_only_fields = ["id", "timestamp"]
