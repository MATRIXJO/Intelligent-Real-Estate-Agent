# keyword_weights.py
import re

# Seed keyword weights (affect score boost). 
# Format: "keyword": (Livability_Boost, Investment_Boost)
# Positive = Good, Negative = Bad
KEYWORD_WEIGHTS = {
    # --- INFRASTRUCTURE & CONNECTIVITY ---
    "metro": (2.0, 1.5),
    "near metro": (2.5, 1.5), # Specific phrase gets higher score, handled by logic below
    "airport": (0.5, 2.0),    # Far for living, great for investment growth
    "ring road": (1.0, 1.5),
    "orr": (1.5, 2.0),        # Outer Ring Road is gold for investment
    "nice road": (0.5, 1.0),
    "highway": (0.0, 1.0),

    # --- AMENITIES ---
    "gated": (1.5, 0.8),
    "community": (1.0, 0.5),
    "gated community": (2.0, 1.2),
    "clubhouse": (1.5, 0.5),
    "club": (1.0, 0.3),
    "gym": (1.0, 0.3),
    "swimming pool": (1.5, 0.5),
    "pool": (1.0, 0.4),
    "park": (1.5, 0.5),
    "garden": (1.2, 0.4),
    "lake": (1.5, 1.0),       # Lake view is premium
    "security": (1.5, 0.5),
    "cctv": (1.0, 0.2),

    # --- UTILITIES (Crucial for Bangalore) ---
    "cauvery": (3.0, 1.5),          # Huge livability factor
    "kaveri": (3.0, 1.5),           # Spelling variation
    "borewell": (1.0, 0.5),
    "water supply": (1.0, 0.5),
    "power backup": (1.5, 0.5),
    
    # --- LEGAL & STATUS ---
    "a khata": (1.5, 2.0),          # Critical for resale/loan
    "e khata": (1.0, 1.5),
    "b khata": (-1.0, -1.0),        # Risky
    "dc conversion": (0.5, 1.0),
    "oc received": (2.0, 1.5),      # Safe bet
    "ready to move": (2.5, 1.0),    # High livability, lower growth potential than pre-launch
    "under construction": (-2.0, 2.5), # Bad for immediate living, GREAT for investment appreciation
    "new launch": (-1.0, 3.0),      # Best for investment
    "resale": (1.0, 0.0),

    # --- PROPERTY FEATURES ---
    "corner": (1.0, 1.5),           # Corner plots demand premium
    "east facing": (1.5, 1.0),      # Vastu compliance
    "north facing": (1.0, 0.8),     # Vastu compliance
    "vastu": (1.0, 0.5),
    "furnished": (2.0, 0.5),
    "semi furnished": (1.0, 0.2),
    "duplex": (1.5, 1.0),
    "villa": (2.0, 1.5),
    "balcony": (0.5, 0.1),
    "luxury": (1.5, 1.0),

    # --- LOCATION PROXIMITY ---
    "school": (1.5, 0.5),
    "hospital": (1.5, 0.5),
    "tech park": (1.0, 2.0),
    "it hub": (1.0, 2.0),
    "mall": (1.0, 0.5),
    "market": (0.8, 0.2)
}

def compute_keyword_scores(text: str):
    """
    Returns (livability_boost, investment_boost) derived from keywords.
    Uses Regex Word Boundaries to prevent substring matching issues.
    """
    if not text or not isinstance(text, str):
        return 0.0, 0.0
    
    # Normalize text
    t = text.lower()
    
    liv = 0.0
    inv = 0.0
    
    # Track matched words to avoid double counting (e.g. "Near Metro" and "Metro")
    # We iterate by key length descending (longest phrases first)
    sorted_keys = sorted(KEYWORD_WEIGHTS.keys(), key=len, reverse=True)
    
    # We mask the text as we find matches so we don't match substrings later
    # E.g. if we find "gated community", we remove it so "community" doesn't trigger again.
    temp_text = t 

    for kw in sorted_keys:
        # Regex \b ensures word boundaries. 
        # e.g. matches "park" but NOT "parking" or "sparkling"
        # re.escape handles special chars like "+" or "."
        pattern = r'\b' + re.escape(kw) + r'\b'
        
        if re.search(pattern, temp_text):
            l_boost, i_boost = KEYWORD_WEIGHTS[kw]
            liv += l_boost
            inv += i_boost
            
            # Remove the found keyword from temp_text to prevent double counting overlapping words
            temp_text = re.sub(pattern, " ", temp_text)

    # Cap the boost to reasonable limits (+/- 15 to allow for strong signals)
    liv = max(min(liv, 15.0), -5.0)
    inv = max(min(inv, 15.0), -5.0)
    
    return liv, inv
