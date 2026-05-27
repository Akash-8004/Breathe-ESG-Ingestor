"""
Ingestion models — DataSource, IngestionRun, RawRecord.

Core principle: every ingested row becomes an immutable RawRecord,
which is then mapped to a mutable EmissionEntry.
"""
from django.db import models
from django.conf import settings


class DataSource(models.Model):
    """
    Represents a configured data integration source for a tenant.
    """
    SOURCE_TYPE_CHOICES = [
        ('SAP', 'SAP Fuel & Procurement'),
        ('UTILITY', 'Utility Electricity'),
        ('TRAVEL', 'Corporate Travel'),
    ]

    tenant = models.ForeignKey(
        'users.Tenant',
        on_delete=models.CASCADE,
        related_name='data_sources',
    )
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['tenant', 'name']

    def __str__(self):
        return f"{self.name} ({self.source_type}) — {self.tenant.name}"


class IngestionRun(models.Model):
    """
    One run = one file upload. Tracks processing status, row counts, and errors.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETE', 'Complete'),
        ('FAILED', 'Failed'),
    ]

    data_source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name='ingestion_runs',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ingestion_runs',
    )
    triggered_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_log = models.TextField(blank=True, default='')
    raw_file = models.FileField(upload_to='ingestion_files/', null=True, blank=True)
    row_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-triggered_at']

    def __str__(self):
        return f"Run #{self.id} — {self.data_source.source_type} — {self.status}"

    @property
    def tenant(self):
        return self.data_source.tenant


class RawRecord(models.Model):
    """
    Immutable, append-only record of exactly what came in from the source.
    Never edited after creation — serves as the audit source of truth.
    """
    PARSE_STATUS_CHOICES = [
        ('OK', 'OK'),
        ('PARSE_ERROR', 'Parse Error'),
        ('VALIDATION_ERROR', 'Validation Error'),
    ]

    ingestion_run = models.ForeignKey(
        IngestionRun,
        on_delete=models.CASCADE,
        related_name='raw_records',
    )
    row_index = models.IntegerField()
    raw_payload = models.JSONField()
    parse_status = models.CharField(
        max_length=20,
        choices=PARSE_STATUS_CHOICES,
        default='OK',
    )
    parse_error = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['row_index']
        unique_together = ['ingestion_run', 'row_index']

    def __str__(self):
        return f"Row {self.row_index} — {self.parse_status}"
