import pandas as pd
import re

# 1. Load your file
df = pd.read_csv('../dataset/listings_final.csv')

def calculate_exact_price(price_str):
    # Return None if empty or "Price on Request"
    if not isinstance(price_str, str) or "Request" in price_str:
        return None

    # Clean basic characters
    clean_str = price_str.replace('₹', '').replace(',', ', ') 
    
    groups = clean_str.split(',')
    group_averages = []

    for group in groups:
        parts = group.split('-')
        parts_values = []
        
        for part in parts:
            part = part.strip()
            if not part: continue
            
            # Extract number
            number_match = re.search(r"(\d+\.?\d*)", part)
            if not number_match: continue
            val = float(number_match.group(1))
            
            # Normalize everything to CRORES first
            # If 'L' is found, divide by 100 (80L = 0.8Cr)
            if 'L' in part:
                val = val / 100 
            elif 'Cr' in part:
                pass 
            elif 'Cr' in group and 'L' not in group: 
                pass 
            elif 'L' in group:
                 if group.strip().endswith('L'):
                     val = val / 100
            
            parts_values.append(val)
        
        if parts_values:
            # Average of the range
            group_averages.append(sum(parts_values) / len(parts_values))

    if not group_averages:
        return None

    # Average of all groups in Crores
    avg_crores = sum(group_averages) / len(group_averages)
    
    # CONVERT TO EXACT NUMBER (Multiply by 10,000,000)
    exact_value = avg_crores * 10000000
    
    # Return as integer to remove decimals
    return int(round(exact_value))

# 2. Apply the function
df['Exact_Price'] = df['price'].apply(calculate_exact_price)

# 3. Save to CSV
# formatting float_format to ensure no scientific notation is written
df.to_csv('my_updated_exact.csv', index=False, float_format='%.0f')

print("Processed successfully.")
