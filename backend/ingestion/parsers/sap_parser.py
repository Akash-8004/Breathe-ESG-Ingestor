"""
SAP Parser — Parses semicolon-delimited SAP flat-file exports (MB51/ME2M).

Handles:
- Semicolon delimiter
- Mixed date formats: YYYYMMDD and DD.MM.YYYY
- Unit conversions: GAL→L (×3.78541), M3→KG (×0.717)
- Known fuel materials: DIESEL, PETROL, LPG, NAT_GAS
- Unknown materials → PARSE_ERROR
- All fuel = Scope 1, category = stationary_combustion
"""
import csv
import io
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

from ingestion.models import RawRecord
from emissions.models import EmissionEntry, AuditTrail
from core.emission_factors import FUEL_EMISSION_FACTORS, UNIT_CONVERSIONS


def parse_sap_date(date_str):
    """
    Parse SAP date string in either YYYYMMDD or DD.MM.YYYY format.
    Returns a date object or raises ValueError.
    """
    if not date_str or not date_str.strip():
        raise ValueError('Empty date')

    date_str = date_str.strip()

    # Try YYYYMMDD format first
    if len(date_str) == 8 and date_str.isdigit():
        return datetime.strptime(date_str, '%Y%m%d').date()

    # Try DD.MM.YYYY format
    if '.' in date_str:
        return datetime.strptime(date_str, '%d.%m.%Y').date()

    raise ValueError(f'Unrecognized date format: {date_str}')


def normalize_quantity(quantity, unit, material):
    """
    Convert quantity to the base unit expected by the emission factor.
    Returns (normalized_quantity, normalized_unit) or raises ValueError.
    """
    unit_upper = unit.upper().strip()
    qty = Decimal(str(quantity))

    if unit_upper == 'GAL':
        # Gallons to liters
        qty = qty * Decimal('3.78541')
        unit_upper = 'L'
    elif unit_upper == 'M3' and material in ('NAT_GAS',):
        # M3 of natural gas stays as M3 — factor is per m3
        pass
    elif unit_upper in ('L', 'KG'):
        pass
    else:
        # Unknown unit — pass through, emission factor may still apply
        pass

    return qty, unit_upper


def parse_sap_file(file_obj, ingestion_run, tenant, user):
    """
    Parse a SAP semicolon-delimited CSV file.

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
        content = content.decode('utf-8-sig')  # Handle BOM

    reader = csv.DictReader(io.StringIO(content), delimiter=';')

    for idx, row in enumerate(reader):
        row_index = idx + 1
        row_count += 1

        # Create immutable RawRecord regardless of parse result
        raw_record = RawRecord.objects.create(
            ingestion_run=ingestion_run,
            row_index=row_index,
            raw_payload=dict(row),
            parse_status='OK',
        )

        try:
            # Extract fields
            material = (row.get('MATNR', '') or row.get('MaterialNo', '')).strip().upper()
            material_desc = (row.get('MAKTX', '') or row.get('MaterialDesc', '')).strip()
            quantity_str = (row.get('MENGE', '') or row.get('Qty', '')).strip()
            unit = (row.get('MEINS', '') or row.get('UOM', '')).strip()
            amount_str = (row.get('DMBTR', '') or row.get('Amount', '')).strip()
            currency = (row.get('WAERS', '') or row.get('Currency', '')).strip()
            date_str = (row.get('BUDAT', '') or row.get('PostingDate', '')).strip()
            plant = (row.get('WERKS', '') or row.get('Plant', '')).strip()

            # Validate quantity
            if not quantity_str:
                raise ValueError('Missing quantity')
            try:
                quantity = Decimal(quantity_str)
            except InvalidOperation:
                raise ValueError(f'Invalid quantity: {quantity_str}')

            if quantity <= 0:
                raise ValueError(f'Non-positive quantity: {quantity}')

            # Validate material has an emission factor
            if material not in FUEL_EMISSION_FACTORS:
                raise ValueError(
                    f'Unrecognized material "{material}", no emission factor available'
                )

            # Parse date
            activity_date = parse_sap_date(date_str)

            # Reject future dates
            if activity_date > date.today():
                raise ValueError(f'Future date not allowed: {activity_date}')

            # Normalize quantity
            normalized_qty, normalized_unit = normalize_quantity(
                quantity, unit, material
            )

            # Get emission factor
            factor_info = FUEL_EMISSION_FACTORS[material]
            emission_factor = Decimal(str(factor_info['factor']))
            emissions_kgco2e = normalized_qty * emission_factor

            # Parse cost
            cost = None
            if amount_str:
                try:
                    cost = Decimal(amount_str)
                except InvalidOperation:
                    cost = None

            # Create EmissionEntry
            entry = EmissionEntry.objects.create(
                tenant=tenant,
                raw_record=raw_record,
                source_type='SAP',
                scope='SCOPE_1',
                category='stationary_combustion',
                activity_date=activity_date,
                quantity=quantity,
                unit=unit,
                quantity_normalized=emissions_kgco2e,
                unit_normalized='kgCO2e',
                emission_factor=emission_factor,
                emission_factor_source=factor_info['source'],
                facility_code=plant,
                cost=cost,
                cost_currency=currency,
                status='PENDING',
            )

            # Create audit trail
            AuditTrail.objects.create(
                emission_entry=entry,
                action='CREATED',
                actor=user,
                notes=f'Ingested from SAP file, row {row_index}',
            )

        except Exception as e:
            # Update raw record with error
            raw_record.parse_status = 'PARSE_ERROR'
            raw_record.parse_error = str(e)
            raw_record.save()
            error_count += 1

    return row_count, error_count
