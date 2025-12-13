import json
from config import GROQ_MODEL
from fallback_extractor import extract_all as fallback_extract, parse_budget
from locality_map import infer_zone_from_locality

def extract_filters_llm(client, query_text: str, history_str: str = ""):
    """
    Extracts filters using Groq (Llama-3).
    """
    # 1. Fallback first
    fallback_data = fallback_extract(query_text)

    if not client:
        return fallback_data

    # 2. Prompt
    system_msg = """
    You are a real estate query parser. 
    Extract search filters from the User Query and Conversation History into a JSON object.
    
    Rules:
    - "bhk": List of integers (e.g., [2, 3]). Null if not found.
    - "budget_max": The maximum price mentioned. Return the raw number or string. Null if not found.
    - "locality": Specific area name. Null if not found.
    
    Output JSON ONLY.
    """
    
    user_msg = f"""
    Conversation History:
    {history_str}
    
    User Query: "{query_text}"
    """

    try:
        # GROQ CALL
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            # Llama-3 supports JSON mode
            response_format={"type": "json_object"}, 
            temperature=0
        )
        
        text = response.choices[0].message.content
        llm_data = json.loads(text)

        # --- 3. MERGING LOGIC (Same as before) ---
        final_locality = llm_data.get("locality") or fallback_data.get("locality")
        if final_locality and final_locality.lower() in ["bangalore", "bengaluru", "location"]:
            final_locality = None

        final_zone = None
        if final_locality:
            final_zone = infer_zone_from_locality(final_locality)

        llm_budget_raw = llm_data.get("budget_max")
        if llm_budget_raw:
            final_budget = parse_budget(str(llm_budget_raw))
        else:
            final_budget = fallback_data.get("budget_max")

        final_bhk = llm_data.get("bhk") or fallback_data.get("bhk")

        return {
            "bhk": final_bhk,
            "budget_max": final_budget,
            "locality": final_locality,
            "zone": final_zone
        }

    except Exception as e:
        print(f"⚠️ Groq Extraction failed: {e}")
        return fallback_data
