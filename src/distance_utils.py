# distance_utils.py
import math
from typing import Tuple

EARTH_RADIUS_KM = 6371.0

def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Haversine formula to compute distance in kilometers between two lat/lon points.
    """
    if None in (lat1, lon1, lat2, lon2):
        return float("inf")
    rlat1, rlon1 = math.radians(lat1), math.radians(lon1)
    rlat2, rlon2 = math.radians(lat2), math.radians(lon2)
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat/2)**2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return EARTH_RADIUS_KM * c

def is_within_radius(lat1: float, lon1: float, lat2: float, lon2: float, radius_km: float) -> bool:
    """
    Return True if distance <= radius_km.
    """
    return distance_km(lat1, lon1, lat2, lon2) <= float(radius_km)

