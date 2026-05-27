"""
IATA airport coordinate lookup for Haversine distance calculations.

Used when corporate travel data has origin/destination airport codes
but no distance in kilometers. Only includes airports specified in the
assignment scope.
"""

AIRPORT_COORDINATES = {
    'BOM': {
        'name': 'Mumbai — Chhatrapati Shivaji Maharaj International',
        'lat': 19.0896,
        'lon': 72.8656,
    },
    'DEL': {
        'name': 'Delhi — Indira Gandhi International',
        'lat': 28.5562,
        'lon': 77.1000,
    },
    'LHR': {
        'name': 'London — Heathrow',
        'lat': 51.4706,
        'lon': -0.4619,
    },
    'JFK': {
        'name': 'New York — John F. Kennedy International',
        'lat': 40.6413,
        'lon': -73.7781,
    },
    'DXB': {
        'name': 'Dubai — Dubai International',
        'lat': 25.2532,
        'lon': 55.3657,
    },
    'SIN': {
        'name': 'Singapore — Changi',
        'lat': 1.3644,
        'lon': 103.9915,
    },
    'SFO': {
        'name': 'San Francisco — San Francisco International',
        'lat': 37.6213,
        'lon': -122.3790,
    },
    'CDG': {
        'name': 'Paris — Charles de Gaulle',
        'lat': 49.0097,
        'lon': 2.5479,
    },
}


def get_airport_coords(iata_code):
    """
    Returns (lat, lon) tuple for a known IATA code, or None if unknown.
    """
    airport = AIRPORT_COORDINATES.get(iata_code.upper().strip() if iata_code else '')
    if airport:
        return airport['lat'], airport['lon']
    return None
