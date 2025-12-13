import pandas as pd
import re
import numpy as np

# 1. Load your file
df = pd.read_csv('my_updated.csv')

# Helper function to clean strings and find averages
def calculate_avg_from_list(num_list):
    if not num_list:
        return None
    # Remove commas and convert to float
    cleaned_nums = [float(n.replace(',', '')) for n in num_list]
    return sum(cleaned_nums) / len(cleaned_nums)

# Core logic function
def process_area(row):
    # Check if 'area' column is NOT empty/NaN
    if pd.notna(row['area']) and str(row['area']).strip() != '':
        # Extract numbers from the 'area' column (handles "1,600 sqft" and "1200-1400")
        matches = re.findall(r'(\d[\d,]*)', str(row['area']))
        return calculate_avg_from_list(matches)
    
    # If 'area' IS empty, look in 'description'
    else:
        desc = str(row['description'])
        # Regex to find numbers immediately followed by area keywords (sqft, sq.ft, sft, etc.)
        # It ignores numbers like "3 BHK" or "2nd Floor"
        pattern = r'(\d[\d,]*)\s*(?:sq\.?\s*ft|sft|sq\.?\s*meter|sq\.?\s*yds)'
        matches = re.findall(pattern, desc, re.IGNORECASE)
        
        return calculate_avg_from_list(matches)

# 2. Apply the function to create the new column
df['Cleaned_Area'] = df.apply(process_area, axis=1)

# 3. Save the updated file
df.to_csv('my_updated.csv', index=False)

print("Extraction complete. Saved to 'my_updated.csv'")
print(df[['area', 'Cleaned_Area']].head())
