import uuid

from django.core.validators import EmailValidator
from django.db import models
from django.db.models.functions import Lower

from users.models import CustomUser, Organization


class TargetTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="target_tags"
    )
    name = models.CharField(max_length=100)
    color = models.CharField(
        max_length=7, default="#007bff", help_text="Hex color code"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "target_tags"
        unique_together = ["organization", "name"]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class Target(models.Model):
    RISK_LEVEL_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="targets"
    )
    email = models.EmailField(validators=[EmailValidator()])
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True)
    risk_level = models.CharField(
        max_length=20, choices=RISK_LEVEL_CHOICES, default="medium"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField(TargetTag, blank=True, related_name="targets")

    class Meta:
        db_table = "targets"

        ordering = ["last_name", "first_name"]
        constraints = [
            models.UniqueConstraint(
                Lower("email"), "organization", name="uq_targets_org_email_ci"
            )
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class TargetGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="target_groups"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    targets = models.ManyToManyField(Target, blank=True, related_name="groups")
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="created_target_groups"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "target_groups"
        unique_together = ["organization", "name"]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.targets.count()} targets)"


class TargetImport(models.Model):
    STATUS_CHOICES = [
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="target_imports"
    )
    file_name = models.CharField(max_length=255)
    total_records = models.IntegerField()
    successful_imports = models.IntegerField(default=0)
    failed_imports = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_log = models.TextField(blank=True)
    imported_by = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="target_imports"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "target_imports"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Import: {self.file_name} ({self.status})"
