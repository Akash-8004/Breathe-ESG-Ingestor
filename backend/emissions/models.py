"""
Emissions models — EmissionEntry and AuditTrail.

EmissionEntry is the normalized, mutable (pre-approval) record computed
from a RawRecord. AuditTrail is append-only, written automatically on
every status change.
"""
from django.db import models
from django.conf import settings


class EmissionEntry(models.Model):
    """
    Normalized emission record computed from a RawRecord.
    Mutable only until approved — after approval, changes are rejected.
    """
    SOURCE_TYPE_CHOICES = [
        ('SAP', 'SAP'),
        ('UTILITY', 'Utility'),
        ('TRAVEL', 'Travel'),
    ]
    SCOPE_CHOICES = [
        ('SCOPE_1', 'Scope 1 — Direct Emissions'),
        ('SCOPE_2', 'Scope 2 — Indirect (Energy)'),
        ('SCOPE_3', 'Scope 3 — Other Indirect'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('FLAGGED', 'Flagged for Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    tenant = models.ForeignKey(
        'users.Tenant',
        on_delete=models.CASCADE,
        related_name='emission_entries',
    )
    raw_record = models.OneToOneField(
        'ingestion.RawRecord',
        on_delete=models.CASCADE,
        related_name='emission_entry',
    )
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES)
    category = models.CharField(
        max_length=100,
        help_text='e.g. stationary_combustion, purchased_electricity, air_travel',
    )
    activity_date = models.DateField(null=True, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    # Original values
    quantity = models.DecimalField(max_digits=18, decimal_places=6)
    unit = models.CharField(max_length=50, help_text='Original unit e.g. liters, kWh, km')

    # Normalized values
    quantity_normalized = models.DecimalField(
        max_digits=18, decimal_places=6,
        help_text='Emission quantity in kgCO2e',
    )
    unit_normalized = models.CharField(
        max_length=20, default='kgCO2e',
        help_text='Always kgCO2e',
    )

    # Emission factor used
    emission_factor = models.DecimalField(max_digits=18, decimal_places=8)
    emission_factor_source = models.CharField(
        max_length=255,
        help_text='e.g. DEFRA 2023, CEA 2022',
    )

    # Location & facility
    location = models.CharField(max_length=255, blank=True, default='')
    facility_code = models.CharField(max_length=100, blank=True, default='')

    # Cost
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_currency = models.CharField(max_length=10, blank=True, default='')

    # Review status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
    )
    flagged_reason = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-activity_date', '-created_at']
        verbose_name_plural = 'Emission entries'

    def __str__(self):
        return (
            f"{self.source_type} | {self.scope} | "
            f"{self.quantity_normalized} kgCO2e | {self.status}"
        )


class AuditTrail(models.Model):
    """
    Append-only audit trail for EmissionEntry status changes.
    Written automatically — never deleted.
    """
    ACTION_CHOICES = [
        ('CREATED', 'Created'),
        ('FLAGGED', 'Flagged'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    emission_entry = models.ForeignKey(
        EmissionEntry,
        on_delete=models.CASCADE,
        related_name='audit_trail',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_actions',
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        actor_name = self.actor.username if self.actor else 'System'
        return f"{self.action} by {actor_name} at {self.timestamp}"
