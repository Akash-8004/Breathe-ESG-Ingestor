"""
Utility Parser — Parses utility portal CSV exports for electricity consumption.

Handles:
- Mixed kWh and MWh (MWh → kWh × 1000)
- Null Consumption computed from MeterReading - PreviousReading
- Overlapping billing periods for same MeterID → FLAGGED
- Scope 2, category = purchased_electricity
- Emission factor: 0.82 kgCO2e/kWh (CEA 2022)
"""
import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation
from collections import defaultdict

from ingestion.models import RawRecord
from emissions.models import EmissionEntry, AuditTrail
from core.emission_factors import ELECTRICITY_FACTOR


def parse_date(date_str):
    """Parse date from common utility bill formats."""
    if not date_str or not date_str.strip():
        return None

    date_str = date_str.strip()

    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    raise ValueError(f'Unrecognized date format: {date_str}')


def check_overlapping_periods(meter_periods, meter_id, period_start, period_end):
    """
    Check if the given billing period overlaps with any existing period
    for the same meter. Returns overlapping period info or None.
    """
    for existing_start, existing_end in meter_periods.get(meter_id, []):
        # Two periods overlap if one starts before the other ends
        if period_start <= existing_end and period_end >= existing_start:
            return (existing_start, existing_end)
    return None


def parse_utility_file(file_obj, ingestion_run, tenant, user):
    """
    Parse a utility portal CSV file.

    Args:
        file_obj: File-like object (uploaded CSV)
        ingestion_run: IngestionRun instance
        tenant: Tenant instance
        user: User who triggered the ingestion

    Returns:
        (row_count, error_count) tuple
    """
    row_count = 0
    error_count = 0

    content = file_obj.read()
    if isinstance(content, bytes):
        content = content.decode('utf-8-sig')

    reader = csv.DictReader(io.StringIO(content))

    # Track billing periods per meter for overlap detection
    meter_periods = defaultdict(list)
    # Store entries for post-processing overlap detection
    entries_to_check = []

    for idx, row in enumerate(reader):
        row_index = idx + 1
        row_count += 1

        raw_record = RawRecord.objects.create(
            ingestion_run=ingestion_run,
            row_index=row_index,
            raw_payload=dict(row),
            parse_status='OK',
        )

        try:
            # Extract fields
            meter_id = (row.get('MeterID', '') or '').strip()
            service_address = (row.get('ServiceAddress', '') or '').strip()
            account_number = (row.get('AccountNumber', '') or '').strip()

            period_start_str = (row.get('BillingPeriodStart', '') or '').strip()
            period_end_str = (row.get('BillingPeriodEnd', '') or '').strip()
            reading_date_str = (row.get('ReadingDate', '') or '').strip()

            meter_reading_str = (row.get('MeterReading', '') or '').strip()
            prev_reading_str = (row.get('PreviousReading', '') or '').strip()
            consumption_str = (row.get('Consumption', '') or '').strip()
            units = (row.get('Units', '') or '').strip().upper()

            billed_amount_str = (row.get('BilledAmount', '') or '').strip()
            currency = (row.get('Currency', '') or '').strip()

            # Parse dates
            period_start = parse_date(period_start_str)
            period_end = parse_date(period_end_str)
            reading_date = parse_date(reading_date_str)

            if not period_start or not period_end:
                raise ValueError('Missing billing period dates')

            activity_date = reading_date or period_end

            # Parse consumption — compute from readings if null
            consumption = None
            if consumption_str:
                try:
                    consumption = Decimal(consumption_str)
                except InvalidOperation:
                    consumption = None

            if consumption is None:
                # Try to compute from meter readings
                if meter_reading_str and prev_reading_str:
                    try:
                        meter_reading = Decimal(meter_reading_str)
                        prev_reading = Decimal(prev_reading_str)
                        consumption = meter_reading - prev_reading
                    except InvalidOperation:
                        raise ValueError(
                            'Null consumption and invalid meter readings — '
                            'cannot compute consumption'
                        )
                else:
                    raise ValueError(
                        'Null consumption and missing meter readings — '
                        'cannot compute consumption'
                    )

            if consumption <= 0:
                raise ValueError(f'Non-positive consumption: {consumption}')

            # Unit normalization: MWh → kWh
            if units == 'MWH':
                consumption = consumption * Decimal('1000')
                units = 'KWH'
            elif units not in ('KWH', ''):
                units = 'KWH'  # Assume kWh if unspecified

            # Calculate emissions
            factor = Decimal(str(ELECTRICITY_FACTOR['factor']))
            emissions_kgco2e = consumption * factor

            # Parse cost
            cost = None
            if billed_amount_str:
                try:
                    cost = Decimal(billed_amount_str)
                except InvalidOperation:
                    cost = None

            # Check for overlapping billing periods
            flagged_reason = ''
            status = 'PENDING'
            overlap = check_overlapping_periods(
                meter_periods, meter_id, period_start, period_end
            )
            if overlap:
                status = 'FLAGGED'
                flagged_reason = (
                    f'Overlapping billing period detected for meter {meter_id}: '
                    f'this period ({period_start} to {period_end}) overlaps with '
                    f'existing period ({overlap[0]} to {overlap[1]}). '
                    f'This may be a bill correction.'
                )

            # Track this period
            meter_periods[meter_id].append((period_start, period_end))

            # Create EmissionEntry
            entry = EmissionEntry.objects.create(
                tenant=tenant,
                raw_record=raw_record,
                source_type='UTILITY',
                scope='SCOPE_2',
                category='purchased_electricity',
                activity_date=activity_date,
                period_start=period_start,
                period_end=period_end,
                quantity=consumption,
                unit='kWh',
                quantity_normalized=emissions_kgco2e,
                unit_normalized='kgCO2e',
                emission_factor=factor,
                emission_factor_source=ELECTRICITY_FACTOR['source'],
                location=service_address,
                facility_code=meter_id,
                cost=cost,
                cost_currency=currency,
                status=status,
                flagged_reason=flagged_reason,
            )

            # Create audit trail
            action = 'FLAGGED' if status == 'FLAGGED' else 'CREATED'
            AuditTrail.objects.create(
                emission_entry=entry,
                action=action,
                actor=user,
                notes=(
                    flagged_reason if flagged_reason
                    else f'Ingested from utility file, row {row_index}'
                ),
            )

        except Exception as e:
            raw_record.parse_status = 'PARSE_ERROR'
            raw_record.parse_error = str(e)
            raw_record.save()
            error_count += 1

    return row_count, error_count
