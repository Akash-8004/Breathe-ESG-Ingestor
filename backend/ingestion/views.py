"""
Ingestion views — IngestionRun CRUD, RawRecord listing, DataSource listing.

All querysets scoped by request.user.tenant.
"""
from django.utils import timezone
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import DataSource, IngestionRun, RawRecord
from .serializers import (
    DataSourceSerializer,
    IngestionRunListSerializer,
    IngestionRunDetailSerializer,
    IngestionRunCreateSerializer,
    RawRecordSerializer,
)
from .parsers.sap_parser import parse_sap_file
from .parsers.utility_parser import parse_utility_file
from .parsers.travel_parser import parse_travel_file


PARSER_MAP = {
    'SAP': parse_sap_file,
    'UTILITY': parse_utility_file,
    'TRAVEL': parse_travel_file,
}

SOURCE_NAMES = {
    'SAP': 'SAP Fuel Export',
    'UTILITY': 'Utility Electricity',
    'TRAVEL': 'Corporate Travel',
}


class DataSourceListView(generics.ListAPIView):
    """GET /api/data-sources/ — List data sources for tenant."""
    serializer_class = DataSourceSerializer

    def get_queryset(self):
        return DataSource.objects.filter(tenant=self.request.user.tenant)


class IngestionRunViewSet(viewsets.ViewSet):
    """
    GET  /api/ingestion-runs/                  → list all runs for tenant
    POST /api/ingestion-runs/                  → upload file + source_type, triggers parsing
    GET  /api/ingestion-runs/{id}/             → run detail
    GET  /api/ingestion-runs/{id}/raw-records/ → paginated raw records
    """
    parser_classes = [MultiPartParser, FormParser]

    def list(self, request):
        """List all ingestion runs for the user's tenant."""
        tenant = request.user.tenant
        runs = IngestionRun.objects.filter(
            data_source__tenant=tenant
        ).select_related('data_source', 'triggered_by')
        serializer = IngestionRunListSerializer(runs, many=True)
        return Response(serializer.data)

    def create(self, request):
        """Upload a file and trigger parsing."""
        serializer = IngestionRunCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data['file']
        source_type = serializer.validated_data['source_type']
        tenant = request.user.tenant

        if not tenant:
            return Response(
                {'error': 'User has no tenant assigned.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get or create data source for this tenant + source_type
        data_source, _ = DataSource.objects.get_or_create(
            tenant=tenant,
            source_type=source_type,
            defaults={'name': SOURCE_NAMES.get(source_type, source_type)},
        )

        # Create ingestion run
        run = IngestionRun.objects.create(
            data_source=data_source,
            status='PROCESSING',
            triggered_by=request.user,
            raw_file=uploaded_file,
        )

        # Parse the file
        parser_func = PARSER_MAP.get(source_type)
        if not parser_func:
            run.status = 'FAILED'
            run.error_log = f'No parser available for source type: {source_type}'
            run.completed_at = timezone.now()
            run.save()
            return Response(
                {'error': f'No parser for source type: {source_type}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Reset file position for parser
            uploaded_file.seek(0)
            row_count, error_count = parser_func(
                uploaded_file, run, tenant, request.user
            )
            run.status = 'COMPLETE'
            run.row_count = row_count
            run.error_count = error_count
            run.completed_at = timezone.now()
            run.save()
        except Exception as e:
            run.status = 'FAILED'
            run.error_log = str(e)
            run.completed_at = timezone.now()
            run.save()
            return Response(
                {'error': f'Ingestion failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            IngestionRunDetailSerializer(run).data,
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        """Get ingestion run detail."""
        tenant = request.user.tenant
        try:
            run = IngestionRun.objects.select_related(
                'data_source', 'triggered_by'
            ).get(pk=pk, data_source__tenant=tenant)
        except IngestionRun.DoesNotExist:
            return Response(
                {'error': 'Ingestion run not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(IngestionRunDetailSerializer(run).data)


class RawRecordListView(generics.ListAPIView):
    """GET /api/ingestion-runs/{run_id}/raw-records/ — paginated raw records."""
    serializer_class = RawRecordSerializer

    def get_queryset(self):
        run_id = self.kwargs['run_id']
        tenant = self.request.user.tenant
        return RawRecord.objects.filter(
            ingestion_run_id=run_id,
            ingestion_run__data_source__tenant=tenant,
        )
