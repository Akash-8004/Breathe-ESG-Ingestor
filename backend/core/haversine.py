"""
Haversine formula — calculates great-circle distance between two
points on Earth given their latitude and longitude in decimal degrees.

Used for computing flight distances when only airport codes are available.
"""
from math import radians, cos, sin, asin, sqrt

EARTH_RADIUS_KM = 6371.0


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance in kilometers between two points
    on Earth (specified in decimal degrees).

    Args:
        lat1, lon1: Latitude and longitude of point 1
        lat2, lon2: Latitude and longitude of point 2

    Returns:
        Distance in kilometers (float)
    """
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))

    return EARTH_RADIUS_KM * c
