"""
Centralized emission factors — hardcoded DEFRA 2023, CEA 2022, and HCMI values.

All factors are in kgCO2e per the specified unit.
A production system would use a versioned factor database; these hardcoded values
are correct enough for a prototype and fully auditable.
"""

# =============================================================================
# Scope 1 — Stationary Combustion (Fuel Materials)
# Source: DEFRA 2023 UK Government GHG Conversion Factors
# =============================================================================
FUEL_EMISSION_FACTORS = {
    'DIESEL': {
        'factor': 2.68,           # kgCO2e per liter
        'unit': 'L',
        'source': 'DEFRA 2023 — Fuels, Liquid fuels, Diesel (average biofuel blend)',
    },
    'PETROL': {
        'factor': 2.31,           # kgCO2e per liter
        'unit': 'L',
        'source': 'DEFRA 2023 — Fuels, Liquid fuels, Petrol (average biofuel blend)',
    },
    'LPG': {
        'factor': 1.51,           # kgCO2e per liter
        'unit': 'L',
        'source': 'DEFRA 2023 — Fuels, Gaseous fuels, LPG',
    },
    'NAT_GAS': {
        'factor': 2.04,           # kgCO2e per m3
        'unit': 'M3',
        'source': 'DEFRA 2023 — Fuels, Gaseous fuels, Natural gas',
    },
}

# Unit conversion factors to normalize to the factor's expected unit
UNIT_CONVERSIONS = {
    'GAL': {'to': 'L', 'multiplier': 3.78541},       # US gallons to liters
    'M3': {'to': 'KG', 'multiplier': 0.717},          # m3 of natural gas to kg
    'MWH': {'to': 'KWH', 'multiplier': 1000.0},       # megawatt-hours to kilowatt-hours
}

# =============================================================================
# Scope 2 — Purchased Electricity
# Source: CEA 2022 (Central Electricity Authority, India)
# =============================================================================
ELECTRICITY_FACTOR = {
    'factor': 0.82,               # kgCO2e per kWh
    'unit': 'kWh',
    'source': 'CEA 2022 — India grid average CO2 emission factor',
}

# =============================================================================
# Scope 3 — Business Travel (Flights)
# Source: DEFRA 2023 — Business travel, Flights
# =============================================================================
FLIGHT_EMISSION_FACTORS = {
    'ECONOMY': {
        'factor': 0.255,          # kgCO2e per passenger-km
        'source': 'DEFRA 2023 — Flights, Economy class',
    },
    'BUSINESS': {
        'factor': 0.573,          # kgCO2e per passenger-km
        'source': 'DEFRA 2023 — Flights, Business class',
    },
}

# Short-haul uplift: flights < 1000 km get 15% additional emissions
SHORT_HAUL_THRESHOLD_KM = 1000
SHORT_HAUL_UPLIFT = 1.15

# =============================================================================
# Scope 3 — Business Travel (Hotels, Ground Transport)
# Source: DEFRA 2023 / HCMI
# =============================================================================
HOTEL_FACTOR = {
    'factor': 20.6,               # kgCO2e per room-night
    'unit': 'room-night',
    'source': 'HCMI (Hotel Carbon Measurement Initiative) average',
}

GROUND_TRANSPORT_FACTORS = {
    'TAXI': {
        'factor': 0.21,           # kgCO2e per km
        'default_distance_km': 50,
        'source': 'DEFRA 2023 — Taxi, regular',
    },
    'RENTAL_CAR': {
        'factor': 0.21,           # kgCO2e per km
        'default_distance_km': 50,
        'source': 'DEFRA 2023 — Car (average)',
    },
    'TRAIN': {
        'factor': 0.041,          # kgCO2e per km
        'source': 'DEFRA 2023 — Rail, national rail',
    },
}
