# filters_extractor.py
import re
import json
from typing import Dict, Any

# Import your helper modules
from fallback_extractor import extract_all as fallback_extract, parse_budget
from locality_map import infer_zone_from_locality, LOCALITY_TO_ZONE

def extract_filters_llm(co_client, query_text: str, model="command-r-plus-08-2024"):
    """
    Hybrid Extraction: Combines the linguistic power of Cohere 
    with the precision of Python regex.
    """
    
    # 1. Run Rule-Based Extraction First (Fast & Precise for numbers)
    # We will use this to validate or fill gaps in the LLM response
    fallback_data = fallback_extract(query_text)

    if not co_client:
        return fallback_data

    # 2. Refined Prompt with Edge Cases
    prompt = f"""
    You are a real estate query parser. Extract search filters into JSON.
    
    User Query: "{query_text}"
    
    Rules:
    - "bhk": List of integers (e.g., "2.5 BHK" -> [2, 3], "3 bedroom" -> [3]). Null if not found.
    - "budget_max": The maximum price mentioned. Return the raw number/string found (e.g., "1.5 Cr", "80 Lakhs"). Null if not found.
    - "locality": The specific area name (e.g. "Whitefield"). Null if not found.
    
    Output JSON ONLY:
    {{
      "bhk": [2, 3],
      "budget_max": "1.5 Cr",
      "locality": "Whitefield"
    }}
    """

    try:
        resp = co_client.chat(
            model=model,
            message=prompt,
            temperature=0,
            connectors=[]
        )
        text = resp.text.strip()
        
        # Robust JSON extraction (finds { ... } pattern)
        m = re.search(r'\{[\s\S]*\}', text)
        if m:
            llm_data = json.loads(m.group(0))
        else:
            llm_data = json.loads(text) # Try parsing raw if regex failed

        # --- 3. INTELLIGENT MERGING ---
        
        # A. Locality: LLM is better at identifying locations in messy text
        # Use LLM locality if found, else fallback
        final_locality = llm_data.get("locality") or fallback_data.get("locality")
        
        # Cleanup locality: Ensure it's not just "Bangalore"
        if final_locality and final_locality.lower() in ["bangalore", "bengaluru"]:
            final_locality = None

        # B. Zone: ALWAYS infer from your master map to ensure DB consistency
        # Never trust the LLM's internal geography logic over your database keys
        final_zone = None
        if final_locality:
            final_zone = infer_zone_from_locality(final_locality)

        # C. Budget: LLM finds the string, Python calculates the Integer
        # If LLM extracted "1.5 Cr", pass that string to your parser
        llm_budget_raw = llm_data.get("budget_max")
        if llm_budget_raw:
            # Convert LLM's string/int to standard int using your logic
            final_budget = parse_budget(str(llm_budget_raw))
        else:
            final_budget = fallback_data.get("budget_max")

        # D. BHK: LLM is usually good at "2 or 3 bhk" logic
        final_bhk = llm_data.get("bhk") or fallback_data.get("bhk")

        return {
            "bhk": final_bhk,
            "budget_max": final_budget,
            "locality": final_locality,
            "zone": final_zone
        }

    except Exception as e:
        print(f"LLM Extraction failed: {e}. Reverting to Regex.")
        return fallback_data
