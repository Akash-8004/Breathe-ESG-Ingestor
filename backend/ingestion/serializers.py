"""
Ingestion serializers — DataSource, IngestionRun, RawRecord.
"""
from rest_framework import serializers
from .models import DataSource, IngestionRun, RawRecord


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = ['id', 'name', 'source_type', 'config', 'created_at']
        read_only_fields = ['id', 'created_at']


class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = [
            'id', 'ingestion_run', 'row_index', 'raw_payload',
            'parse_status', 'parse_error', 'created_at',
        ]
        read_only_fields = fields


class IngestionRunListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    source_type = serializers.CharField(source='data_source.source_type', read_only=True)
    source_name = serializers.CharField(source='data_source.name', read_only=True)
    triggered_by_name = serializers.CharField(
        source='triggered_by.username', read_only=True, default=''
    )

    class Meta:
        model = IngestionRun
        fields = [
            'id', 'source_type', 'source_name', 'status',
            'triggered_by_name', 'triggered_at', 'completed_at',
            'row_count', 'error_count',
        ]
        read_only_fields = fields


class IngestionRunDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer including error log."""
    source_type = serializers.CharField(source='data_source.source_type', read_only=True)
    source_name = serializers.CharField(source='data_source.name', read_only=True)
    triggered_by_name = serializers.CharField(
        source='triggered_by.username', read_only=True, default=''
    )

    class Meta:
        model = IngestionRun
        fields = [
            'id', 'source_type', 'source_name', 'status',
            'triggered_by_name', 'triggered_at', 'completed_at',
            'error_log', 'row_count', 'error_count',
        ]
        read_only_fields = fields


class IngestionRunCreateSerializer(serializers.Serializer):
    """Serializer for creating an ingestion run via file upload."""
    file = serializers.FileField()
    source_type = serializers.ChoiceField(choices=['SAP', 'UTILITY', 'TRAVEL'])
