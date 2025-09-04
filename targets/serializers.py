from django.core.validators import EmailValidator
from rest_framework import serializers

from users.models import CustomUser

from .models import Target, TargetGroup, TargetImport, TargetTag

ALLOWED_FIELDS = {
    "email",
    "first_name",
    "last_name",
    "department",
    "job_title",
    "phone",
    "risk_level",
    "is_active",
}


class TargetTagSerializer(serializers.ModelSerializer):
    targets_count = serializers.SerializerMethodField()

    class Meta:
        model = TargetTag
        fields = ["id", "name", "color", "created_at", "targets_count"]
        read_only_fields = ["id", "created_at", "targets_count"]

    def get_targets_count(self, obj):
        return obj.targets.count()

    def create(self, validated_data):
        validated_data["organization"] = self.context["request"].user.organization
        return super().create(validated_data)


class TargetSerializer(serializers.ModelSerializer):
    tags = TargetTagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=TargetTag.objects.all(), required=False
    )

    class Meta:
        model = Target
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "department",
            "job_title",
            "phone",
            "risk_level",
            "is_active",
            "created_at",
            "tags",
            "tag_ids",
            "full_name",
        ]
        read_only_fields = ["id", "created_at", "full_name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and hasattr(request.user, "organization"):
            self.fields["tag_ids"].queryset = TargetTag.objects.filter(
                organization=request.user.organization
            )

    def create(self, validated_data):
        tag_ids = validated_data.pop("tag_ids", [])
        validated_data["organization"] = self.context["request"].user.organization
        target = Target.objects.create(**validated_data)
        target.tags.set(tag_ids)
        return target

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop("tag_ids", None)
        instance = super().update(instance, validated_data)

        if tag_ids is not None:
            instance.tags.set(tag_ids)

        return instance


class TargetBulkCreateSerializer(serializers.Serializer):
    targets = serializers.ListField(child=serializers.DictField(), allow_empty=False)

    def validate_targets(self, value):
        validated = []
        errors = []

        for i, target_data in enumerate(value):
            try:
                # email required
                if "email" not in target_data or not target_data["email"]:
                    errors.append(f"Row {i+1}: Email is required")
                    continue

                # normalize + validate email
                email = str(target_data["email"]).strip().lower()
                EmailValidator()(email)

                row = {
                    k: target_data.get(k) for k in ALLOWED_FIELDS if k in target_data
                }
                row["email"] = email
                row.setdefault("risk_level", "medium")
                row.setdefault("is_active", True)

                validated.append(row)

            except Exception as e:
                errors.append(f"Row {i+1}: {str(e)}")

        if errors:
            raise serializers.ValidationError(errors)

        return validated


class TargetGroupSerializer(serializers.ModelSerializer):
    targets = TargetSerializer(many=True, read_only=True)
    target_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Target.objects.all(), required=False
    )
    targets_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )

    class Meta:
        model = TargetGroup
        fields = [
            "id",
            "name",
            "description",
            "targets",
            "target_ids",
            "targets_count",
            "created_by",
            "created_by_name",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "targets_count", "created_by"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and hasattr(request.user, "organization"):

            self.fields["target_ids"].queryset = Target.objects.filter(
                organization=request.user.organization
            )

    def get_targets_count(self, obj):
        return obj.targets.count()

    def create(self, validated_data):
        target_ids = validated_data.pop("target_ids", [])
        validated_data["organization"] = self.context["request"].user.organization
        validated_data["created_by"] = self.context["request"].user

        group = TargetGroup.objects.create(**validated_data)
        group.targets.set(target_ids)
        return group

    def update(self, instance, validated_data):
        target_ids = validated_data.pop("target_ids", None)
        instance = super().update(instance, validated_data)

        if target_ids is not None:
            instance.targets.set(target_ids)

        return instance


class TargetImportSerializer(serializers.ModelSerializer):
    imported_by_name = serializers.CharField(
        source="imported_by.get_full_name", read_only=True
    )
    success_rate = serializers.SerializerMethodField()

    class Meta:
        model = TargetImport
        fields = [
            "id",
            "file_name",
            "total_records",
            "successful_imports",
            "failed_imports",
            "status",
            "error_log",
            "imported_by",
            "imported_by_name",
            "created_at",
            "success_rate",
        ]
        read_only_fields = ["id", "created_at", "imported_by"]

    def get_success_rate(self, obj):
        if obj.total_records > 0:
            return round((obj.successful_imports / obj.total_records) * 100, 2)
        return 0
