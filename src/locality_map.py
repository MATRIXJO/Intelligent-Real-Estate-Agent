# locality_map.py
import re

# Comprehensive mapping of Bangalore localities to Zones
# Keys must be lowercase for the matching logic.
LOCALITY_TO_ZONE = {
    # --- NORTH ---
    "devanahalli": "North",
    "yelahanka": "North",
    "hebbal": "North",
    "thanisandra": "North",
    "jakkur": "North",
    "bagalur": "North",
    "hennur": "North",
    "sahakara nagar": "North",
    "vidyaranyapura": "North",
    "rt nagar": "North",
    "peenya": "North",
    "yeshwanthpur": "North",
    "jalahalli": "North",
    "mathikere": "North",
    "sanjay nagar": "North",
    "nagawara": "North",
    "kogilu": "North",
    "doddaballapur": "North",
    "chikkajala": "North",
    "kalyan nagar": "North",
    "hrbr layout": "North",
    "hbr layout": "North",
    "banaswadi": "North",
    "horamavu": "North",
    "kothanur": "North",
    "hessarghatta": "North",
    "nelamangala": "North",
    "manyata": "North",
    "bel road": "North",
    
    # --- EAST ---
    "whitefield": "East",
    "sarjapur": "East",
    "varthur": "East",
    "marathahalli": "East",
    "kr puram": "East",
    "mahadevapura": "East",
    "bellandur": "East",
    "brookefield": "East",
    "kundalahalli": "East",
    "hoodi": "East",
    "budigere": "East",
    "hoskote": "East",
    "old madras road": "East",
    "old airport road": "East",
    "cv raman nagar": "East",
    "kaggadasapura": "East",
    "kadugodi": "East",
    "panathur": "East",
    "gunjur": "East",
    "ramamurthy nagar": "East",
    "kasturi nagar": "East",
    "itpl": "East",
    "aecs layout": "East",
    "beml layout": "East",
    "bidarahalli": "East",
    "seegehalli": "East",
    "thubarahalli": "East",

    # --- SOUTH ---
    "electronic city": "South",
    "electronics city": "South",
    "koramangala": "South",
    "hsr layout": "South",
    "btm layout": "South",
    "jayanagar": "South",
    "jp nagar": "South",
    "bannerghatta": "South",
    "kanakapura": "South",
    "hosur road": "South",
    "begur": "South",
    "bommanahalli": "South",
    "basavanagudi": "South",
    "padmanabhanagar": "South",
    "kumaraswamy layout": "South",
    "uttarahalli": "South",
    "banashankari": "South",
    "arekere": "South",
    "hulimavu": "South",
    "gottigere": "South",
    "jigani": "South",
    "anekal": "South",
    "attibele": "South",
    "chandapura": "South",
    "harlur": "South",
    "kudlu": "South",
    "singasandra": "South",
    "konanakunte": "South",
    "billekahalli": "South",

    # --- WEST ---
    "malleshwaram": "West",
    "rajajinagar": "West",
    "vijayanagar": "West",
    "basaveshwara nagar": "West",
    "nagarbhavi": "West",
    "kengeri": "West",
    "mysore road": "West",
    "magadi road": "West",
    "chandra layout": "West",
    "mahalakshmi layout": "West",
    "nandini layout": "West",
    "rr nagar": "West",
    "rajarajeshwari nagar": "West",
    "kumbalgodu": "West",
    "bidadi": "West",
    "nayandahalli": "West",

    # --- CENTRAL ---
    "mg road": "Central",
    "brigade road": "Central",
    "cunningham road": "Central",
    "lavelle road": "Central",
    "richmond": "Central",
    "vasanth nagar": "Central",
    "shivajinagar": "Central",
    "frazer town": "Central",
    "benson town": "Central",
    "ulsoor": "Central",
    "halasuru": "Central",
    "shanthi nagar": "Central",
    "wilson garden": "Central",
    "seshadripuram": "Central",
    "majestic": "Central",
    "chamarajpet": "Central",
    "domlur": "Central", # Sometimes classified as East, but centrally located
    "indiranagar": "Central", # Geographically East-Central, often grouped with Central for premium value
    "ashok nagar": "Central"
}

# Pre-sort keys by length (Longest first) to ensure specific matches are found before general ones.
# Example: "Electronic City Phase 1" will be matched before "Electronic City"
SORTED_LOCALITIES = sorted(LOCALITY_TO_ZONE.keys(), key=len, reverse=True)

def infer_zone_from_locality(locality: str):
    """
    Infers the zone based on the locality string.
    """
    if not locality or not isinstance(locality, str):
        return "Unknown"

    # Normalize: lowercase and remove special characters (keep alphanumeric and spaces)
    clean_text = locality.lower().strip()
    
    # 1. Exact Match Check (Fastest)
    if clean_text in LOCALITY_TO_ZONE:
        return LOCALITY_TO_ZONE[clean_text]

    # 2. Substring Match (Longest string first)
    for loc in SORTED_LOCALITIES:
        # We check if the locality key exists in the input text
        if loc in clean_text:
            return LOCALITY_TO_ZONE[loc]
    
    return "Unknown"
