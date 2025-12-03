# fuzzy_locality.py
from rapidfuzz import process, fuzz
from typing import Tuple, Optional

# Expect locality_coords.py to define LOCALITY_COORDS: Dict[str, (lat,lon)]
try:
    from locality_coords import LOCALITY_COORDS
except Exception:
    LOCALITY_COORDS = {}  # fallback

# Prebuild choices for rapidfuzz
_CHOICES = list(LOCALITY_COORDS.keys())

def get_coords_for_locality(query: str, threshold: int = 65) -> Tuple[Optional[float], Optional[float], Optional[str], float]:
    """
    Return (lat, lon, matched_name, score)
    - query: user typed locality (free text)
    - threshold: min similarity score to accept a fuzzy match (0-100)
    If no match above threshold, returns (None, None, None, 0.0)
    """
    if not query or not isinstance(query, str):
        return None, None, None, 0.0

    q = query.strip().lower()

    # Exact match quick path
    if q in LOCALITY_COORDS:
        lat, lon = LOCALITY_COORDS[q]
        return lat, lon, q, 100.0

    # Use RapidFuzz to find best candidate
    if not _CHOICES:
        return None, None, None, 0.0

    match = process.extractOne(q, _CHOICES, scorer=fuzz.token_sort_ratio)
    if not match:
        return None, None, None, 0.0

    matched_name, score, _ = match  # score between 0-100
    if score < threshold:
        # return best but indicate low confidence
        return None, None, None, float(score)

    lat, lon = LOCALITY_COORDS.get(matched_name)
    return lat, lon, matched_name, float(score)

