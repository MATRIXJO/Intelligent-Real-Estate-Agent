import pandas as pd
import json
import os
from pathlib import Path
from config import DATA_CSV, DOCS_JSONL

def safe_get(row, col, default=''):
    val = row.get(col)
    if pd.isna(val) or val == "" or str(val).lower() == "nan":
        return default
    return val

def parse_bhk_string(bhk_str):
    """Parses '[2, 3]' string into a Python list."""
    if pd.isna(bhk_str) or str(bhk_str) == '[]':
        return []
    try:
        clean = str(bhk_str).replace('[', '').replace(']', '')
        # Handle floats like '2.0' converting to int '2'
        return [int(float(x.strip())) for x in clean.split(',') if x.strip()]
    except:
        return []

def format_price(price_val):
    try:
        val = float(price_val)
        if val >= 10000000: return f"{val/10000000:.2f} Cr"
        elif val >= 100000: return f"{val/100000:.2f} Lakhs"
        return str(int(val))
    except:
        return "Price on Request"

def row_to_doc(row):
    title = safe_get(row, 'title', 'Untitled Property')
    locality = safe_get(row, 'Extracted_Locality', 'Bangalore')
    zone = safe_get(row, 'Zone', 'Unknown')
    
    price_raw = row.get('Exact_Price', 0)
    price_fmt = format_price(price_raw)
    
    # Clean Area: Ensure it's a number
    area_val = row.get('Cleaned_Area', 0)
    try:
        area = float(area_val)
    except:
        area = 0.0
    
    price_per_sqft = row.get('Price_Per_Sqft', 0) if pd.notna(row.get('Price_Per_Sqft')) else 0.0
    # BHK Handling
    bhk_list = parse_bhk_string(row.get('BHK_List', '[]'))
    bhk_text = ", ".join([str(x) for x in bhk_list]) if bhk_list else "Residential"

    liv_score = round(float(row.get('Livability_Score', 0)), 1)
    inv_score = round(float(row.get('Investment_Score', 0)), 1)

    # Rich Text for Embedding
    text_parts = [
        f"Real Estate Listing: {title}.",
        f"Located in {locality}, {zone} Zone, Bangalore.",
        f"This property offers {bhk_text} BHK configurations.",
        f"Priced at approximately {price_fmt} for an area of {area} sqft.",
        f"Scores: Livability {liv_score}/100, Investment Potential {inv_score}/100."
    ]
    
    desc = safe_get(row, 'description')
    if desc:
        clean_desc = " ".join(str(desc).split())
        text_parts.append(f"Details: {clean_desc}")

    full_text = " ".join(text_parts)

    # Metadata - Convert Lists to Strings for Chroma Compatibility
    metadata = {
        "title": str(title),
        "url": str(safe_get(row, 'url', '')),
        "locality": str(locality),
        "zone": str(zone),
        "exact_price": float(price_raw) if pd.notna(price_raw) else 0.0,
        "area": area,
        "price_per_sqft": float(price_per_sqft),
        "bhk_list": str(bhk_list), # Stored as string "[2, 3]" for Chroma
        "livability_score": float(liv_score),
        "investment_score": float(inv_score)
    }

    return {
        "id": str(row.name),
        "text": full_text, 
        "metadata": metadata
    }

def build_docs():
    print(f"Reading from {DATA_CSV}...")
    df = pd.read_csv(DATA_CSV)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(DOCS_JSONL), exist_ok=True)
    
    count = 0
    with open(DOCS_JSONL, "w", encoding="utf8") as f:
        for _, r in df.iterrows():
            doc = row_to_doc(r)
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
            count += 1
            
    print(f"Successfully wrote {count} documents to: {DOCS_JSONL}")

if __name__ == "__main__":
    build_docs()
