import re
from typing import Optional, List

# Import the specific map we created earlier
# Ensure locality_map.py is in the same folder
try:
    from locality_map import LOCALITY_TO_ZONE, SORTED_LOCALITIES
except ImportError:
    # Fallback if file missing (for standalone testing)
    LOCALITY_TO_ZONE = {} 
    SORTED_LOCALITIES = []

CURRENCY_MAP = {
    "cr": 10000000, "crore": 10000000, "crores": 10000000,
    "lakh": 100000, "lakhs": 100000, "l": 100000, "lac": 100000, "lacs": 100000,
    "k": 1000
}

WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6
}

def parse_budget(text: str) -> Optional[int]:
    if not text: return None
    s = text.lower().replace(",", "") # Remove commas immediately
    
    # 1. Explicit matches (Number + Unit) - e.g., "1.5 cr", "80 lakhs"
    # We look for specific units to avoid confusion with sqft/bhk
    m = re.search(r'(\d+(?:\.\d+)?)\s*(cr|crore|lakh|lac|l|k)\b', s)
    
    if m:
        val = float(m.group(1))
        unit = m.group(2)
        # Normalize unit strings
        if unit.startswith("cr"): mul = 10000000
        elif unit.startswith("l"): mul = 100000
        elif unit == "k": mul = 1000
        else: mul = 1
        return int(val * mul)

    # 2. Implicit Context (e.g., "budget 5000000")
    # Only look for raw large numbers if 'budget' or 'price' is mentioned nearby
    # or if the number is very large (> 5 Lakhs)
    large_nums = re.findall(r'\b(\d{6,})\b', s)
    if large_nums:
        return int(large_nums[0]) # Return the first large number found
        
    return None

def parse_bhk(text: str) -> Optional[List[int]]:
    if not text: return None
    s = text.lower()
    
    # Convert words to numbers (e.g. "three bhk" -> "3 bhk")
    for word, num in WORD_TO_NUM.items():
        s = s.replace(word, str(num))

    bhks = set()

    # 1. Handle "2.5 BHK" specific case
    if "2.5" in s:
        # usually mapped to 3 in search or kept as special case. 
        # For this logic, we might treat it as 3 or keep 2. 
        # Let's append 2 and 3 to be safe, or just 3.
        bhks.add(3) 

    # 2. Ranges: "2 to 3 BHK", "2-3 BHK"
    m_range = re.search(r'(\d+)\s*(?:-|to)\s*(\d+)\s*(?:bhk|bed)', s)
    if m_range:
        start = int(m_range.group(1))
        end = int(m_range.group(2))
        # Safety cap to prevent "1200 sqft" acting as range end
        if start < 10 and end < 10:
            return list(range(start, end + 1))

    # 3. Multiple choices: "2, 3 BHK", "2 or 3 BHK"
    # Find all digits immediately preceding "bhk" or "bedroom"
    # This regex looks for patterns like "2, 3, 4 BHK"
    # It creates a temporary string focusing on the area around the keyword
    if "bhk" in s or "bed" in s:
        # Extract simple integers < 10 to avoid capturing sqft or budget
        candidates = re.findall(r'\b(\d)\b', s)
        for c in candidates:
            bhks.add(int(c))

    # If specific "BHK" token exists, prioritize numbers attached to it
    # e.g. "3BHK"
    attached = re.findall(r'(\d)bhk', s)
    for a in attached:
        bhks.add(int(a))

    if not bhks:
        if "studio" in s:
            return [1]
        return None

    return sorted(list(bhks))

def parse_locality_and_zone(text: str):
    """
    Scans the text for known localities from our database.
    Returns (locality, zone)
    """
    if not text: return None, None
    s = text.lower()
    
    # Remove common noise words to prevent false partial matches if any
    # (Optional, but 'whitefield' match is usually safe)
    
    # Iterate through our SORTED keys (Longest first)
    # This comes from locality_map.py
    for loc in SORTED_LOCALITIES:
        # Check if the known locality is in the query string
        # Use \b for word boundary to avoid matching 'male' in 'maleshwaram'
        if re.search(r'\b' + re.escape(loc) + r'\b', s):
            return loc.title(), LOCALITY_TO_ZONE[loc]
            
    return None, None

def extract_all(text: str):
    """
    Returns dict: {"bhk": [..], "budget_max": int, "locality": str, "zone": str}
    """
    bhk = parse_bhk(text)
    budget = parse_budget(text)
    loc, zone = parse_locality_and_zone(text)
    
    return {
        "bhk": bhk,
        "budget_max": budget,
        "locality": loc,
        "zone": zone
    }
