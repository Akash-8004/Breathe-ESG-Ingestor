"""
Travel Parser — Parses corporate travel CSV exports (Concur/Navan style).

Handles three expense types:
- Flights: DistanceKM if present, else Haversine from IATA codes, else PARSE_ERROR
  - Economy 0.255 kgCO2e/km, Business 0.573 kgCO2e/km
  - Short-haul (<1000km) ×1.15 uplift
- Hotels: 20.6 kgCO2e per room-night
- Ground transport (Taxi, Rental Car, Train): per-km factors with 50km default

All travel = Scope 3, category = business_travel
"""
import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

from ingestion.models import RawRecord
from emissions.models import EmissionEntry, AuditTrail
from core.emission_factors import (
    FLIGHT_EMISSION_FACTORS,
    SHORT_HAUL_THRESHOLD_KM,
    SHORT_HAUL_UPLIFT,
    HOTEL_FACTOR,
    GROUND_TRANSPORT_FACTORS,
)
from core.iata_data import get_airport_coords
from core.haversine import haversine


def parse_travel_date(date_str):
    """Parse travel date from common formats."""
    if not date_str or not date_str.strip():
        return None

    date_str = date_str.strip()
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    raise ValueError(f'Unrecognized date format: {date_str}')


def compute_flight_distance(row):
    """
    Compute flight distance in km.
    Priority: DistanceKM field → Haversine from IATA codes → error
    Returns (distance_km, method_note) or raises ValueError.
    """
    distance_str = (row.get('DistanceKM', '') or '').strip()

    if distance_str:
        try:
            distance = float(distance_str)
            if distance > 0:
                return distance, 'from_data'
        except ValueError:
            pass

    # Fallback to Haversine
    origin_code = (row.get('OriginCode', '') or '').strip().upper()
    dest_code = (row.get('DestCode', '') or '').strip().upper()

    if not origin_code or not dest_code:
        raise ValueError(
            f'Missing flight distance and incomplete airport codes '
            f'(origin={origin_code or "EMPTY"}, dest={dest_code or "EMPTY"})'
        )

    origin_coords = get_airport_coords(origin_code)
    dest_coords = get_airport_coords(dest_code)

    if not origin_coords:
        raise ValueError(f'Unknown origin airport code: {origin_code}')
    if not dest_coords:
        raise ValueError(f'Unknown destination airport code: {dest_code}')

    distance = haversine(
        origin_coords[0], origin_coords[1],
        dest_coords[0], dest_coords[1],
    )
    return distance, f'haversine({origin_code}->{dest_code})'


def process_flight(row, raw_record, tenant, user, row_index):
    """Process a flight expense row."""
    distance_km, distance_method = compute_flight_distance(row)

    cabin_class = (row.get('CabinClass', '') or '').strip().upper()
    if 'BUSINESS' in cabin_class:
        cabin_key = 'BUSINESS'
    else:
        cabin_key = 'ECONOMY'

    factor_info = FLIGHT_EMISSION_FACTORS[cabin_key]
    factor = Decimal(str(factor_info['factor']))

    # Short-haul uplift
    if distance_km < SHORT_HAUL_THRESHOLD_KM:
        factor = factor * Decimal(str(SHORT_HAUL_UPLIFT))
        factor_source = f"{factor_info['source']} + short-haul uplift ×{SHORT_HAUL_UPLIFT}"
    else:
        factor_source = factor_info['source']

    emissions_kgco2e = Decimal(str(distance_km)) * factor

    # Parse cost
    cost_str = (row.get('AmountUSD', '') or '').strip()
    cost = None
    if cost_str:
        try:
            cost = Decimal(cost_str)
        except InvalidOperation:
            cost = None

    origin = (row.get('Origin', '') or '').strip()
    dest = (row.get('Destination', '') or '').strip()

    entry = EmissionEntry.objects.create(
        tenant=tenant,
        raw_record=raw_record,
        source_type='TRAVEL',
        scope='SCOPE_3',
        category='business_travel',
        activity_date=parse_travel_date(row.get('TravelDate', '')),
        quantity=Decimal(str(round(distance_km, 2))),
        unit='km',
        quantity_normalized=emissions_kgco2e,
        unit_normalized='kgCO2e',
        emission_factor=factor,
        emission_factor_source=factor_source,
        location=f'{origin} → {dest}',
        cost=cost,
        cost_currency=row.get('LocalCurrency', 'USD').strip(),
        status='PENDING',
    )

    AuditTrail.objects.create(
        emission_entry=entry,
        action='CREATED',
        actor=user,
        notes=f'Flight {cabin_key}, {distance_km:.0f}km ({distance_method}), row {row_index}',
    )


def process_hotel(row, raw_record, tenant, user, row_index):
    """Process a hotel expense row."""
    nights_str = (row.get('HotelNights', '') or '').strip()
    if not nights_str:
        raise ValueError('Missing HotelNights')

    try:
        nights = int(nights_str)
    except ValueError:
        raise ValueError(f'Invalid HotelNights: {nights_str}')

    if nights <= 0:
        raise ValueError(f'Non-positive hotel nights: {nights}')

    factor = Decimal(str(HOTEL_FACTOR['factor']))
    emissions_kgco2e = Decimal(str(nights)) * factor

    cost_str = (row.get('AmountUSD', '') or '').strip()
    cost = None
    if cost_str:
        try:
            cost = Decimal(cost_str)
        except InvalidOperation:
            cost = None

    hotel_name = (row.get('HotelName', '') or '').strip()
    hotel_city = (row.get('HotelCity', '') or '').strip()

    entry = EmissionEntry.objects.create(
        tenant=tenant,
        raw_record=raw_record,
        source_type='TRAVEL',
        scope='SCOPE_3',
        category='business_travel',
        activity_date=parse_travel_date(row.get('TravelDate', '')),
        quantity=Decimal(str(nights)),
        unit='room-nights',
        quantity_normalized=emissions_kgco2e,
        unit_normalized='kgCO2e',
        emission_factor=factor,
        emission_factor_source=HOTEL_FACTOR['source'],
        location=f'{hotel_name}, {hotel_city}' if hotel_name else hotel_city,
        cost=cost,
        cost_currency=row.get('LocalCurrency', 'USD').strip(),
        status='PENDING',
    )

    AuditTrail.objects.create(
        emission_entry=entry,
        action='CREATED',
        actor=user,
        notes=f'Hotel stay, {nights} nights in {hotel_city}, row {row_index}',
    )


def process_ground_transport(row, raw_record, tenant, user, row_index):
    """Process a ground transport expense row (Taxi, Rental Car, Train)."""
    transport_mode = (row.get('GroundTransportMode', '') or '').strip().upper()

    # Map to factor key
    mode_key = None
    if 'TAXI' in transport_mode:
        mode_key = 'TAXI'
    elif 'RENTAL' in transport_mode or 'CAR' in transport_mode:
        mode_key = 'RENTAL_CAR'
    elif 'TRAIN' in transport_mode:
        mode_key = 'TRAIN'
    else:
        raise ValueError(f'Unknown ground transport mode: {transport_mode}')

    factor_info = GROUND_TRANSPORT_FACTORS[mode_key]
    factor = Decimal(str(factor_info['factor']))

    # Distance
    distance_str = (row.get('DistanceKM', '') or '').strip()
    flagged_reason = ''
    status = 'PENDING'

    if distance_str:
        try:
            distance_km = Decimal(distance_str)
        except InvalidOperation:
            distance_km = Decimal(str(factor_info.get('default_distance_km', 50)))
            flagged_reason = 'distance estimated (invalid value in data)'
            status = 'FLAGGED'
    else:
        default_km = factor_info.get('default_distance_km', 50)
        distance_km = Decimal(str(default_km))
        flagged_reason = f'distance estimated (default {default_km}km used)'
        status = 'FLAGGED'

    emissions_kgco2e = distance_km * factor

    cost_str = (row.get('AmountUSD', '') or '').strip()
    cost = None
    if cost_str:
        try:
            cost = Decimal(cost_str)
        except InvalidOperation:
            cost = None

    entry = EmissionEntry.objects.create(
        tenant=tenant,
        raw_record=raw_record,
        source_type='TRAVEL',
        scope='SCOPE_3',
        category='business_travel',
        activity_date=parse_travel_date(row.get('TravelDate', '')),
        quantity=distance_km,
        unit='km',
        quantity_normalized=emissions_kgco2e,
        unit_normalized='kgCO2e',
        emission_factor=factor,
        emission_factor_source=factor_info['source'],
        location=row.get('Origin', '').strip() or '',
        cost=cost,
        cost_currency=row.get('LocalCurrency', 'USD').strip(),
        status=status,
        flagged_reason=flagged_reason,
    )

    action = 'FLAGGED' if status == 'FLAGGED' else 'CREATED'
    AuditTrail.objects.create(
        emission_entry=entry,
        action=action,
        actor=user,
        notes=(
            flagged_reason if flagged_reason
            else f'{mode_key} transport, {distance_km}km, row {row_index}'
        ),
    )


def parse_travel_file(file_obj, ingestion_run, tenant, user):
    """
    Parse a corporate travel CSV file (Concur/Navan format).

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
            expense_type = (row.get('ExpenseType', '') or '').strip().upper()

            if 'FLIGHT' in expense_type or 'AIR' in expense_type:
                process_flight(row, raw_record, tenant, user, row_index)
            elif 'HOTEL' in expense_type:
                process_hotel(row, raw_record, tenant, user, row_index)
            elif any(t in expense_type for t in ('TAXI', 'CAR', 'RENTAL', 'TRAIN', 'GROUND')):
                process_ground_transport(row, raw_record, tenant, user, row_index)
            else:
                raise ValueError(f'Unknown expense type: {expense_type}')

        except Exception as e:
            raw_record.parse_status = 'PARSE_ERROR'
            raw_record.parse_error = str(e)
            raw_record.save()
            error_count += 1

    return row_count, error_count
