import os
import uuid

from django.conf import settings
from django.db import models


def document_upload_path(instance, filename):
    """
    Physical files are stored under media/documents/<category>/<uuid>_<name>,
    keeping the on-disk name unique regardless of what the user uploaded,
    while the human-readable original name is preserved as a separate
    field on Document. This is what lets storage move to a different
    backend later (rule #21) without touching this naming scheme.
    """
    category_code = instance.category.code if instance.category_id else "uncategorised"
    ext = os.path.splitext(filename)[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return f"documents/{category_code}/{unique_name}"


class DocumentCategory(models.Model):
    """Top-level classification shown in the sidebar (rule #23: Dev / Mass
    filter). Modelled as data, not a hard-coded choices list, so new
    categories can be added without a migration."""

    code = models.SlugField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "Document Categories"

    def __str__(self):
        return self.name


class DocumentType(models.Model):
    """E.g. Engineering, QA, R&D, Production — the middle segment of a
    document code such as DEV-ENG-0142."""

    code = models.SlugField(max_length=30, unique=True)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DocumentSource(models.Model):
    """
    Where the physical file actually lives. Modelling this as its own
    table (rather than a field on Document) is the abstraction rule #22
    asks for: adding a new storage provider is a new row here plus a
    matching branch in services.storage — Document itself never changes.
    """

    class ProviderType(models.TextChoices):
        LOCAL = "local", "Local"
        GOOGLE_DRIVE = "google_drive", "Google Drive"
        SHAREPOINT = "sharepoint", "SharePoint"
        NETWORK_DRIVE = "network_drive", "Network Drive"
        EXTERNAL_URL = "external_url", "External URL"

    name = models.CharField(max_length=100, unique=True)
    provider_type = models.CharField(max_length=30, choices=ProviderType.choices, default=ProviderType.LOCAL)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"


class Document(models.Model):
    """
    Core Document Data record. Metadata lives here in the database;
    the physical bytes live wherever `source` points (rule #21) —
    on local disk for ProviderType.LOCAL, or only as a reference/URL for
    external providers such as Google Drive.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"
        PENDING = "pending", "Pending Review"

    document_code = models.CharField(max_length=60, unique=True, db_index=True)
    document_name = models.CharField(max_length=255)
    category = models.ForeignKey(DocumentCategory, on_delete=models.PROTECT, related_name="documents")
    document_type = models.ForeignKey(
        DocumentType, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents"
    )
    business_unit = models.CharField(max_length=120, blank=True)
    document_year = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="Auto-detected from the code (e.g. SAM-25-... = 2025); editable when the code doesn't carry it.",
    )
    source = models.ForeignKey(DocumentSource, on_delete=models.PROTECT, related_name="documents")

    file = models.FileField(upload_to=document_upload_path, null=True, blank=True)
    external_url = models.URLField(blank=True, help_text="Used when source is not Local (Drive/SharePoint/etc.)")
    file_type = models.CharField(max_length=20, blank=True, help_text="File extension, e.g. pdf, xlsx, docx")
    file_size = models.PositiveBigIntegerField(default=0, help_text="Size in bytes")

    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="documents_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents_updated"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["document_code"]),
            models.Index(fields=["document_name"]),
            models.Index(fields=["-updated_at"]),
            models.Index(fields=["category", "status"]),
        ]
        permissions = [
            ("download_document", "Can download document"),
            ("upload_document", "Can upload document"),
        ]

    def __str__(self):
        return f"{self.document_code} — {self.document_name}"

    @property
    def display_filename(self):
        ext = f".{self.file_type}" if self.file_type else ""
        return f"{self.document_name}{ext}"

    def save(self, *args, **kwargs):
        if self.file and not self.file_type:
            self.file_type = os.path.splitext(self.file.name)[1].lstrip(".").lower()
        if self.file:
            try:
                self.file_size = self.file.size
            except (ValueError, OSError):
                pass
        super().save(*args, **kwargs)


class EquipmentSpec(models.Model):
    """
    One row of the equipment spec list (indoor/outdoor unit models for a
    given year, cross-referenced to that year's Dev and Sam/Mass report
    documents by code). Populated either one row at a time from the web
    form, or in bulk via Excel import — both paths funnel through the
    same model, so the list always reads the same regardless of how a
    row got there.
    """

    year = models.PositiveSmallIntegerField()
    indoor_unit = models.CharField(max_length=500, help_text="Comma-separate multiple indoor models.")
    outdoor_unit = models.CharField(max_length=255, blank=True)
    report_dev_code = models.CharField(max_length=60, blank=True, help_text="Document code of the Dev report, if any.")
    report_sam_code = models.CharField(max_length=60, blank=True, help_text="Document code of the Sam/Mass report, if any.")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="equipment_specs_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="equipment_specs_updated"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["year", "id"]

    def __str__(self):
        return f"{self.year} — {self.indoor_unit}"


class DocumentReport(models.Model):
    """
    Anchors the `report.view` / `report.export` permissions used by the
    (future) reporting screens over Document data. No rows are ever
    created — this model exists purely so those two permissions have a
    content type to attach to, exactly like dashboard.DashboardAccess.
    """

    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ("view_documentreport", "Can view document reports"),
            ("export_documentreport", "Can export document reports"),
        ]
