import csv
import io
from typing import Dict, List

from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import Lower
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from targets.models import Target
from users.permissions import CanManageTargets, IsOrganizationMember

from .models import Target, TargetGroup, TargetImport, TargetTag
from .serializers import (
    TargetBulkCreateSerializer,
    TargetGroupSerializer,
    TargetImportSerializer,
    TargetSerializer,
    TargetTagSerializer,
)

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
RISK_CHOICES = {"low", "medium", "high", "critical"}
MAX_ROWS = 10000
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB


def _coerce_bool(v):
    if isinstance(v, bool):
        return v
    if v is None:
        return None
    s = str(v).strip().lower()
    return (
        True
        if s in {"1", "true", "yes", "y"}
        else False if s in {"0", "false", "no", "n"} else None
    )


def _normalize_row(row: Dict) -> Dict:
    out = {}
    for k, v in row.items():
        if k not in ALLOWED_FIELDS:
            continue
        if isinstance(v, str):
            v = v.strip()
        if k == "email" and isinstance(v, str):
            v = v.strip().lower()
        if k == "risk_level":
            v = (v or "medium").strip().lower()
            if v not in RISK_CHOICES:
                v = "medium"
        if k == "is_active":
            v = _coerce_bool(v)
            if v is None:
                v = True
        out[k] = v
    return out


def _parse_csv(file) -> List[Dict]:
    # Limit read size
    if hasattr(file, "size") and file.size and file.size > MAX_UPLOAD_BYTES:
        raise ValueError("File too large")
    content = file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("File too large")
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for i, row in enumerate(reader, start=1):
        if i > MAX_ROWS:
            raise ValueError(f"Too many rows (>{MAX_ROWS})")
        rows.append(_normalize_row(row))
    return rows


def _parse_excel(file) -> List[Dict]:
    # Lazy import to avoid global pandas cost
    import pandas as pd

    if hasattr(file, "size") and file.size and file.size > MAX_UPLOAD_BYTES:
        raise ValueError("File too large")
    df = pd.read_excel(
        file, dtype=str, engine="openpyxl"
    )  # read-only mode used internally
    # Keep only allowed columns
    keep = [c for c in df.columns if c in ALLOWED_FIELDS]
    df = df[keep]
    if len(df) > MAX_ROWS:
        raise ValueError(f"Too many rows (>{MAX_ROWS})")
    # Normalize each row
    return [_normalize_row(rec) for rec in df.to_dict(orient="records")]


class TargetListView(generics.ListCreateAPIView):
    serializer_class = TargetSerializer
    permission_classes = [CanManageTargets]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["risk_level", "is_active", "department"]
    search_fields = ["first_name", "last_name", "email", "department", "job_title"]
    ordering_fields = ["last_name", "first_name", "email", "created_at"]
    ordering = ["last_name", "first_name"]

    def get_queryset(self):
        return Target.objects.filter(
            organization=self.request.user.organization
        ).prefetch_related("tags")

    @swagger_auto_schema(
        responses={201: TargetSerializer}, operation_description="Create a new target"
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TargetDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TargetSerializer
    permission_classes = [CanManageTargets]

    def get_queryset(self):
        return Target.objects.filter(
            organization=self.request.user.organization
        ).prefetch_related("tags")


class TargetBulkCreateView(APIView):
    """Unified endpoint for JSON, CSV, Excel imports with audit logging"""

    permission_classes = [CanManageTargets]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "file": openapi.Schema(
                    type=openapi.TYPE_FILE, description="CSV or Excel file"
                ),
                "targets": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_OBJECT),
                    description="JSON list of targets (alternative to file)",
                ),
            },
        ),
        responses={201: "Bulk create successful"},
    )
    def post(self, request):
        errors = []
        created_targets = []
        org = request.user.organization
        total_records = 0

        try:
            # 1) Parse input
            if "file" in request.FILES:
                upload = request.FILES["file"]
                name = (upload.name or "").lower()
                if name.endswith(".csv"):
                    rows = _parse_csv(upload)
                elif name.endswith((".xls", ".xlsx")):
                    rows = _parse_excel(upload)
                else:
                    return Response({"error": "Unsupported file type"}, status=400)
            elif "targets" in request.data:
                base = TargetBulkCreateSerializer(data=request.data)
                if not base.is_valid():
                    return Response(base.errors, status=400)
                rows = base.validated_data["targets"]
            else:
                return Response(
                    {"error": "Provide either 'file' or 'targets'."}, status=400
                )

            total_records = len(rows)
            if not rows:
                return Response(
                    {
                        "created_count": 0,
                        "error_count": 0,
                        "errors": [],
                        "created_targets": [],
                    },
                    status=201,
                )

            # 2) Drop duplicates within the file
            seen_emails = set()
            cleaned = []
            for i, r in enumerate(rows, start=1):
                email = (r.get("email") or "").strip().lower()
                if not email:
                    errors.append(f"Row {i}: email is required")
                    continue
                if email in seen_emails:
                    errors.append(f"Row {i}: duplicate email in file ({email})")
                    continue
                seen_emails.add(email)
                r.setdefault("risk_level", "medium")
                r.setdefault("is_active", True)
                cleaned.append(r)

            if not cleaned:
                self._log_import(
                    org, request.user, total_records, 0, total_records, errors
                )
                return Response(
                    {
                        "created_count": 0,
                        "error_count": len(errors),
                        "errors": errors,
                        "created_targets": [],
                    },
                    status=201,
                )

            # 3) Drop duplicates already in DB
            existing = set(
                Target.objects.filter(organization=org)
                .annotate(le=Lower("email"))
                .values_list("le", flat=True)
            )
            to_create = []
            for r in cleaned:
                if r["email"] in existing:
                    errors.append(f"Email already exists: {r['email']}")
                    continue
                to_create.append(r)

            if not to_create:
                self._log_import(
                    org, request.user, total_records, 0, len(errors), errors
                )
                return Response(
                    {
                        "created_count": 0,
                        "error_count": len(errors),
                        "errors": errors,
                        "created_targets": [],
                    },
                    status=201,
                )

            # 4) Validate with TargetSerializer
            valid_rows = []
            for r in to_create:
                data = {k: r.get(k) for k in ALLOWED_FIELDS}
                data["organization"] = org.id
                s = TargetSerializer(data=data)
                if s.is_valid():
                    valid_rows.append(s.validated_data)
                else:
                    errors.append(f"{r.get('email','(no email)')}: {s.errors}")

            if not valid_rows:
                self._log_import(
                    org, request.user, total_records, 0, len(errors), errors
                )
                return Response(
                    {
                        "created_count": 0,
                        "error_count": len(errors),
                        "errors": errors,
                        "created_targets": [],
                    },
                    status=201,
                )

            # 5) Create
            with transaction.atomic():
                for v in valid_rows:
                    v["organization"] = org
                    created_targets.append(Target.objects.create(**v))

            # 6) Log import
            self._log_import(
                org,
                request.user,
                total_records,
                len(created_targets),
                len(errors),
                errors,
            )

            return Response(
                {
                    "created_count": len(created_targets),
                    "error_count": len(errors),
                    "errors": errors[:100],  # cap error messages
                    "created_targets": TargetSerializer(
                        created_targets, many=True
                    ).data,
                },
                status=201,
            )

        except ValueError as ve:
            return Response({"error": str(ve)}, status=400)
        except Exception:
            return Response(
                {"error": "Import failed due to an unexpected error."}, status=500
            )

    def _log_import(self, org, user, total, success, failed, errors):
        TargetImport.objects.create(
            organization=org,
            imported_by=user,
            total_records=total,
            success_count=success,
            failed_count=failed,
            error_log="\n".join(errors[:500]),  # cap error log
        )


class TargetGroupListView(generics.ListCreateAPIView):
    serializer_class = TargetGroupSerializer
    permission_classes = [CanManageTargets]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        return TargetGroup.objects.filter(
            organization=self.request.user.organization
        ).prefetch_related("targets", "created_by")


class TargetGroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TargetGroupSerializer
    permission_classes = [CanManageTargets]

    def get_queryset(self):
        return TargetGroup.objects.filter(
            organization=self.request.user.organization
        ).prefetch_related("targets", "created_by")


class TargetTagListView(generics.ListCreateAPIView):
    serializer_class = TargetTagSerializer
    permission_classes = [CanManageTargets]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering = ["name"]

    def get_queryset(self):
        return TargetTag.objects.filter(organization=self.request.user.organization)


class TargetTagDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TargetTagSerializer
    permission_classes = [CanManageTargets]

    def get_queryset(self):
        return TargetTag.objects.filter(organization=self.request.user.organization)


class TargetImportListView(generics.ListAPIView):
    serializer_class = TargetImportSerializer
    permission_classes = [CanManageTargets]
    ordering = ["-created_at"]

    def get_queryset(self):
        return TargetImport.objects.filter(
            organization=self.request.user.organization
        ).select_related("imported_by")


@swagger_auto_schema(
    method="get",
    responses={200: "Target statistics"},
    operation_description="Get target statistics for dashboard",
)
@api_view(["GET"])
@permission_classes([CanManageTargets])
def target_statistics(request):
    """Get target statistics for dashboard"""
    organization = request.user.organization
    targets_queryset = Target.objects.filter(organization=organization)

    stats = {
        "total_targets": targets_queryset.count(),
        "active_targets": targets_queryset.filter(is_active=True).count(),
        "targets_by_risk": {
            "low": targets_queryset.filter(risk_level="low").count(),
            "medium": targets_queryset.filter(risk_level="medium").count(),
            "high": targets_queryset.filter(risk_level="high").count(),
            "critical": targets_queryset.filter(risk_level="critical").count(),
        },
        "targets_by_department": list(
            targets_queryset.values("department")
            .annotate(count=Count("department"))
            .order_by("-count")[:10]
        ),
        "total_groups": TargetGroup.objects.filter(organization=organization).count(),
        "total_tags": TargetTag.objects.filter(organization=organization).count(),
    }

    return Response(stats)
