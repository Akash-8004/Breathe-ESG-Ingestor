"""
Emissions views — EmissionEntry listing, detail, approve/flag/reject, dashboard.

All querysets scoped by request.user.tenant.
"""
from decimal import Decimal
from django.db.models import Sum, Count, Q
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import EmissionEntry, AuditTrail
from .serializers import (
    EmissionEntryListSerializer,
    EmissionEntryDetailSerializer,
    FlagReasonSerializer,
    DashboardSummarySerializer,
)


class EmissionEntryListView(generics.ListAPIView):
    """
    GET /api/emission-entries/
    Filterable by: status, source_type, scope, date_from, date_to, run_id
    """
    serializer_class = EmissionEntryListSerializer
    pagination_class = None  # Return all entries (no 50-item page limit)

    def get_queryset(self):
        tenant = self.request.user.tenant
        qs = EmissionEntry.objects.filter(tenant=tenant)

        # Apply filters
        params = self.request.query_params

        if params.get('status'):
            qs = qs.filter(status=params['status'])
        if params.get('source_type'):
            qs = qs.filter(source_type=params['source_type'])
        if params.get('scope'):
            qs = qs.filter(scope=params['scope'])
        if params.get('date_from'):
            qs = qs.filter(activity_date__gte=params['date_from'])
        if params.get('date_to'):
            qs = qs.filter(activity_date__lte=params['date_to'])
        if params.get('run_id'):
            qs = qs.filter(raw_record__ingestion_run_id=params['run_id'])

        return qs


class EmissionEntryDetailView(generics.RetrieveAPIView):
    """GET /api/emission-entries/{id}/ — Full detail with raw payload + audit trail."""
    serializer_class = EmissionEntryDetailSerializer

    def get_queryset(self):
        return EmissionEntry.objects.filter(
            tenant=self.request.user.tenant
        ).select_related('raw_record').prefetch_related('audit_trail')


class EmissionEntryApproveView(APIView):
    """POST /api/emission-entries/{id}/approve/"""

    def post(self, request, pk):
        try:
            entry = EmissionEntry.objects.get(
                pk=pk, tenant=request.user.tenant
            )
        except EmissionEntry.DoesNotExist:
            return Response(
                {'error': 'Entry not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if entry.status == 'APPROVED':
            return Response(
                {'error': 'Entry is already approved.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        entry.status = 'APPROVED'
        entry.save()

        AuditTrail.objects.create(
            emission_entry=entry,
            action='APPROVED',
            actor=request.user,
            notes='Approved by analyst',
        )

        return Response(EmissionEntryDetailSerializer(entry).data)


class EmissionEntryFlagView(APIView):
    """POST /api/emission-entries/{id}/flag/ — body: { reason: "..." }"""

    def post(self, request, pk):
        try:
            entry = EmissionEntry.objects.get(
                pk=pk, tenant=request.user.tenant
            )
        except EmissionEntry.DoesNotExist:
            return Response(
                {'error': 'Entry not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = FlagReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data['reason']

        entry.status = 'FLAGGED'
        entry.flagged_reason = reason
        entry.save()

        AuditTrail.objects.create(
            emission_entry=entry,
            action='FLAGGED',
            actor=request.user,
            notes=reason,
        )

        return Response(EmissionEntryDetailSerializer(entry).data)


class EmissionEntryRejectView(APIView):
    """POST /api/emission-entries/{id}/reject/"""

    def post(self, request, pk):
        try:
            entry = EmissionEntry.objects.get(
                pk=pk, tenant=request.user.tenant
            )
        except EmissionEntry.DoesNotExist:
            return Response(
                {'error': 'Entry not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        entry.status = 'REJECTED'
        entry.save()

        AuditTrail.objects.create(
            emission_entry=entry,
            action='REJECTED',
            actor=request.user,
            notes=request.data.get('reason', 'Rejected by analyst'),
        )

        return Response(EmissionEntryDetailSerializer(entry).data)


class DashboardSummaryView(APIView):
    """GET /api/dashboard/summary/ — Aggregated dashboard data."""

    def get(self, request):
        tenant = request.user.tenant
        entries = EmissionEntry.objects.filter(tenant=tenant)

        # Status counts
        status_counts = entries.values('status').annotate(count=Count('id'))
        status_map = {item['status']: item['count'] for item in status_counts}

        # Scope totals
        scope_totals = entries.values('scope').annotate(
            total=Sum('quantity_normalized')
        )
        scope_map = {item['scope']: item['total'] or Decimal('0') for item in scope_totals}

        # Source counts
        source_counts = entries.values('source_type').annotate(count=Count('id'))
        source_map = {item['source_type']: item['count'] for item in source_counts}

        summary = {
            'total_entries': entries.count(),
            'pending_count': status_map.get('PENDING', 0),
            'approved_count': status_map.get('APPROVED', 0),
            'flagged_count': status_map.get('FLAGGED', 0),
            'rejected_count': status_map.get('REJECTED', 0),
            'scope_1_total': scope_map.get('SCOPE_1', Decimal('0')),
            'scope_2_total': scope_map.get('SCOPE_2', Decimal('0')),
            'scope_3_total': scope_map.get('SCOPE_3', Decimal('0')),
            'sap_count': source_map.get('SAP', 0),
            'utility_count': source_map.get('UTILITY', 0),
            'travel_count': source_map.get('TRAVEL', 0),
        }

        return Response(DashboardSummarySerializer(summary).data)
