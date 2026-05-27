"""
Emissions serializers — EmissionEntry and AuditTrail.
"""
from rest_framework import serializers
from .models import EmissionEntry, AuditTrail


class AuditTrailSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.username', read_only=True, default='System')

    class Meta:
        model = AuditTrail
        fields = ['id', 'action', 'actor_name', 'timestamp', 'notes']
        read_only_fields = fields


class EmissionEntryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    class Meta:
        model = EmissionEntry
        fields = [
            'id', 'source_type', 'scope', 'category',
            'activity_date', 'facility_code', 'location',
            'quantity', 'unit', 'quantity_normalized', 'unit_normalized',
            'status', 'flagged_reason',
            'created_at',
        ]
        read_only_fields = fields


class EmissionEntryDetailSerializer(serializers.ModelSerializer):
    """Full serializer including raw payload and audit trail."""
    audit_trail = AuditTrailSerializer(many=True, read_only=True)
    raw_payload = serializers.JSONField(source='raw_record.raw_payload', read_only=True)

    class Meta:
        model = EmissionEntry
        fields = [
            'id', 'tenant', 'source_type', 'scope', 'category',
            'activity_date', 'period_start', 'period_end',
            'quantity', 'unit', 'quantity_normalized', 'unit_normalized',
            'emission_factor', 'emission_factor_source',
            'location', 'facility_code',
            'cost', 'cost_currency',
            'status', 'flagged_reason',
            'created_at', 'updated_at',
            'raw_payload', 'audit_trail',
        ]
        read_only_fields = fields


class FlagReasonSerializer(serializers.Serializer):
    """Serializer for the flag action — requires a reason."""
    reason = serializers.CharField(max_length=1000)


class DashboardSummarySerializer(serializers.Serializer):
    """Dashboard summary data."""
    total_entries = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    approved_count = serializers.IntegerField()
    flagged_count = serializers.IntegerField()
    rejected_count = serializers.IntegerField()
    scope_1_total = serializers.DecimalField(max_digits=18, decimal_places=2)
    scope_2_total = serializers.DecimalField(max_digits=18, decimal_places=2)
    scope_3_total = serializers.DecimalField(max_digits=18, decimal_places=2)
    sap_count = serializers.IntegerField()
    utility_count = serializers.IntegerField()
    travel_count = serializers.IntegerField()
