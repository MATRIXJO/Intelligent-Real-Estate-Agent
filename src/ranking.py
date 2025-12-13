from typing import Dict, Any, Optional
from keyword_weights import compute_keyword_scores
import math

# Base Weights (Sum = 1.0)
BASE_WEIGHTS = {
    "liv": 0.35,
    "inv": 0.35,
    "aff": 0.15, # Affordability
    "sim": 0.15  # Semantic Similarity
}

def calculate_affordability(price: float, budget_max: float) -> float:
    """
    Returns a score 0-10.
    - If Price <= Budget: Score 10 (Perfect)
    - If Price is 10% over Budget: Score 5 (Stretchable)
    - If Price is > 20% over Budget: Score 0 (Too expensive)
    """
    if not budget_max or not price or price <= 0:
        return 5.0 # Neutral if data missing
        
    ratio = price / float(budget_max)

    if ratio <= 1.0:
        return 10.0
    elif ratio <= 1.1: 
        # Linear decay from 10 to 5 for 10% stretch
        # (ratio - 1.0) goes 0.0 -> 0.1
        # 10 - (0.1 * 50) = 5
        return 10.0 - ((ratio - 1.0) * 50.0)
    elif ratio <= 1.2:
        # Linear decay from 5 to 0 for next 10%
        # (ratio - 1.1) goes 0.0 -> 0.1
        return 5.0 - ((ratio - 1.1) * 50.0)
    else:
        return 0.0

def compute_final_score(doc_meta: Dict[str, Any], user_filters: Dict[str, Any], sim_score: float = 0.5) -> float:
    """
    Computes a final 0-100 score dynamically adjusting weights based on available data.
    """
    # 1. Extract & Normalize Data
    # Database scores are 0-100, we scale to 0-10 for calculation
    liv_base = float(doc_meta.get("livability_score", 50.0)) / 10.0
    inv_base = float(doc_meta.get("investment_score", 50.0)) / 10.0
    
    price = float(doc_meta.get("exact_price", 0.0))
    budget = user_filters.get("budget_max")
    
    # 2. Keyword Boosts
    # Combine title and description text
    # We look at 'text' first (standard in RAG), then fallback to title
    raw_text = doc_meta.get("text") or (str(doc_meta.get("title", "")) + " " + str(doc_meta.get("description", "")))
    kw_liv, kw_inv = compute_keyword_scores(raw_text)
    
    # Apply boosts (Scale 0-10)
    # We clamp the result to max 10.0 so keywords don't break the math
    liv_final = min(10.0, liv_base + (kw_liv / 3.0)) # Divide by 3 to control impact
    inv_final = min(10.0, inv_base + (kw_inv / 3.0))
    
    # 3. Calculate Components
    aff_score = calculate_affordability(price, budget)
    sim_score_scaled = sim_score * 10.0 # Convert 0-1 to 0-10
    
    # 4. Dynamic Weighting
    # If user didn't give a budget, set affordability weight to 0 and redistribute
    weights = BASE_WEIGHTS.copy()
    
    if not budget:
        weights["aff"] = 0.0
        # Redistribution factor
        remaining_weight = 1.0 - BASE_WEIGHTS["aff"] # 0.85
        # Scale up others
        weights["liv"] /= remaining_weight
        weights["inv"] /= remaining_weight
        weights["sim"] /= remaining_weight

    # 5. Weighted Sum
    final_score = (
        (weights["liv"] * liv_final) +
        (weights["inv"] * inv_final) +
        (weights["aff"] * aff_score) +
        (weights["sim"] * sim_score_scaled)
    )
    
    # Scale back to 0-100
    return round(final_score * 10.0, 1)
