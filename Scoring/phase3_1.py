#!/usr/bin/env python3
import os
import sys
import json
import re
import pandas as pd
import numpy as np
from collections import Counter

fname = "99_magic_final.csv"
OUTPUT_FILE = "listings_scored_final1.csv"

# Scoring constants
ZONE_LIVABILITY = {"East": 7.5, "South": 9.2, "North": 8.0, "West": 6.8, "Central": 9.5, "Unknown": 5.0}
ZONE_INVESTMENT = {"East": 9.5, "South": 8.2, "North": 9.3, "West": 7.4, "Central": 8.8, "Unknown": 5.0}
BHK_LIV_MAP = {1: 5, 2: 7, 3: 9, 4: 10}
BHK_INV_MAP = {1: 5, 2: 8, 3: 9, 4: 7} 

KEYWORD_WEIGHTS = {
    "gated": 2, "community": 1, "metro": 3, "school": 2,
    "hospital": 1.5, "park": 1.5, "lake": 2, "balcony": 0.5,
    "gym": 1, "club": 1, "luxury": 2, "ready to move": 2,
    "oc received": 3, "khata": 2, "under construction": -0.5
}

# Weights (Must sum to 1.0)
WEIGHTS_LIV = { "area": 0.35, "bhk": 0.25, "zone": 0.20, "price": 0.10, "keyword": 0.10 }
WEIGHTS_INV = { "zone": 0.35, "price": 0.25, "locality": 0.15, "bhk": 0.15, "keyword": 0.10 }

# ---------- Helper Functions ----------

def find_input_file():
    if os.path.exists(fname):
      return fname
    raise FileNotFoundError("No input CSV found.")

def safe_get_col(df, candidates):
    cols = [c.lower() for c in df.columns]
    for cand in candidates:
        if cand.lower() in cols:
            return df.columns[cols.index(cand.lower())]
    return None

def robust_normalize(series, invert=False):
    """
    Normalizes data 0-10 with outlier clipping and median filling for missing values.
    """
    # 1. Convert to numeric, coercing errors to NaN
    s = pd.to_numeric(series, errors='coerce')
    
    # 2. Fill NaNs with Median (Smart Imputation)
    if s.isna().all():
        return pd.Series([5.0] * len(s), index=series.index)
    
    median_val = s.median()
    s = s.fillna(median_val)
    
    # 3. Clip Outliers (5th to 95th percentile)
    # This prevents one massive value from ruining the scale for everyone else
    lower_cap = s.quantile(0.05)
    upper_cap = s.quantile(0.95)
    s_clipped = s.clip(lower_cap, upper_cap)
    
    # 4. Min-Max Scale to 0-10
    s_min = s_clipped.min()
    s_max = s_clipped.max()
    
    if s_max == s_min:
        return pd.Series([5.0] * len(s), index=series.index)
        
    norm = (s_clipped - s_min) / (s_max - s_min) * 10
    
    # 5. Invert if needed (e.g., Price: Lower is better)
    if invert:
        return 10.0 - norm
    return norm

def parse_bhk_list(cell):
    if pd.isna(cell): return []
    if isinstance(cell, list): return cell
    s = str(cell)
    # Extract all digits
    nums = re.findall(r'\d+', s)
    return [int(x) for x in nums]

def compute_keyword_boost(text):
    if pd.isna(text): return 0.0
    t = str(text).lower()
    score = sum([wt for kw, wt in KEYWORD_WEIGHTS.items() if kw in t])
    return min(10.0, score)

# ---------- Main Execution ----------

def main():
    input_file = find_input_file()
    print(f"Processing: {input_file}")
    df = pd.read_csv(input_file)

    # Map columns
    col_area = safe_get_col(df, ["Cleaned_Area", "Area", "sqft"])
    col_price = safe_get_col(df, ["Exact_Price", "Price", "cost"])
    col_ppsf = safe_get_col(df, ["Price_Per_Sqft", "PPSQFT"])
    col_bhk = safe_get_col(df, ["BHK_List", "BHK", "bhk_count"])
    col_zone = safe_get_col(df, ["Zone", "Bangalore_Zone"])
    col_loc = safe_get_col(df, ["Extracted_Locality", "Locality"])
    col_desc = safe_get_col(df, ["description", "desc"])
    col_title = safe_get_col(df, ["title"])

    # --- 1. CALCULATE COMPONENT SCORES ---

    # Area Score
    if col_area:
        df["Score_Area"] = robust_normalize(df[col_area])
    else:
        df["Score_Area"] = 5.0

    # Price Score (Use PPSF if avail, else calculate it, else neutral)
    if not col_ppsf and col_price and col_area:
        df["Calculated_PPSF"] = pd.to_numeric(df[col_price], errors='coerce') / pd.to_numeric(df[col_area], errors='coerce')
        col_ppsf = "Calculated_PPSF"
    
    if col_ppsf:
        # invert=True because Lower Price/Sqft = Higher Score
        df["Score_Price"] = robust_normalize(df[col_ppsf], invert=True)
    else:
        df["Score_Price"] = 5.0

    # BHK Score
    def get_bhk_score(row_val, mode='liv'):
        bhks = parse_bhk_list(row_val)
        if not bhks: return 5.0 # Default neutral if missing
        
        if mode == 'liv':
            # For living, larger is usually better (up to 4)
            val = min(max(bhks), 4)
            return BHK_LIV_MAP.get(val, 6.0)
        else:
            # For investment, 2 and 3 BHKs often sell faster
            if 3 in bhks: return 9.0
            if 2 in bhks: return 8.0
            return 6.0

    if col_bhk:
        df["Score_BHK_Liv"] = df[col_bhk].apply(lambda x: get_bhk_score(x, 'liv'))
        df["Score_BHK_Inv"] = df[col_bhk].apply(lambda x: get_bhk_score(x, 'inv'))
    else:
        df["Score_BHK_Liv"] = 5.0
        df["Score_BHK_Inv"] = 5.0

    # Zone Score
    def get_zone_score(z, map_dict):
        if pd.isna(z): return 5.0
        return map_dict.get(str(z).strip(), 5.0)

    if col_zone:
        df["Score_Zone_Liv"] = df[col_zone].apply(lambda x: get_zone_score(x, ZONE_LIVABILITY))
        df["Score_Zone_Inv"] = df[col_zone].apply(lambda x: get_zone_score(x, ZONE_INVESTMENT))
    else:
        df["Score_Zone_Liv"] = 5.0
        df["Score_Zone_Inv"] = 5.0

    # Keyword Boost
    combo_text = df[col_title].fillna('') + " " + df[col_desc].fillna('')
    df["Score_Keywords"] = combo_text.apply(compute_keyword_boost)

    # Locality Strength (Frequency check)
    if col_loc:
        freqs = df[col_loc].fillna("Unknown").value_counts()
        df["Locality_Freq"] = df[col_loc].map(freqs).fillna(0)
        df["Score_Locality"] = robust_normalize(df["Locality_Freq"])
    else:
        df["Score_Locality"] = 5.0

    # --- 2. HANDLE REMAINING NANS ---
    # This is the fix for your specific issue. 
    # Even with robust logic, sometimes pandas leaves a NaN. We force fill them.
    score_cols = [
        "Score_Area", "Score_Price", "Score_BHK_Liv", "Score_BHK_Inv", 
        "Score_Zone_Liv", "Score_Zone_Inv", "Score_Keywords", "Score_Locality"
    ]
    df[score_cols] = df[score_cols].fillna(5.0)

    # --- 3. FINAL WEIGHTED CALCULATION ---
    
    df["Livability_Score"] = (
        (df["Score_Area"] * WEIGHTS_LIV["area"]) +
        (df["Score_BHK_Liv"] * WEIGHTS_LIV["bhk"]) +
        (df["Score_Zone_Liv"] * WEIGHTS_LIV["zone"]) +
        (df["Score_Price"] * WEIGHTS_LIV["price"]) +
        (df["Score_Keywords"] * WEIGHTS_LIV["keyword"])
    ) * 10

    df["Investment_Score"] = (
        (df["Score_Zone_Inv"] * WEIGHTS_INV["zone"]) +
        (df["Score_Price"] * WEIGHTS_INV["price"]) +
        (df["Score_Locality"] * WEIGHTS_INV["locality"]) +
        (df["Score_BHK_Inv"] * WEIGHTS_INV["bhk"]) +
        (df["Score_Keywords"] * WEIGHTS_INV["keyword"])
    ) * 10

    # Round off
    df["Livability_Score"] = df["Livability_Score"].round(1)
    df["Investment_Score"] = df["Investment_Score"].round(1)
    
    # Final Recommendation (Average)
    df["Recommendation_Score"] = ((df["Livability_Score"] + df["Investment_Score"]) / 2).round(1)

    # --- 4. SAVE ---
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSuccess! Data saved to {OUTPUT_FILE}")
    
    # Verification print
    print(f"Any empty Livability Scores? {df['Livability_Score'].isna().sum()}")
    print(f"Any empty Investment Scores? {df['Investment_Score'].isna().sum()}")
    print("\nSample Output:")
    print(df[["title", "Livability_Score", "Investment_Score"]].head())

if __name__ == "__main__":
    main()
