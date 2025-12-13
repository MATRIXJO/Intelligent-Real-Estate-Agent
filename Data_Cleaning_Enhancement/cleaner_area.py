import pandas as pd
import re

# 1. Load your file (Use the latest file you saved)
input_file = 'my_updated_exact.csv'
df = pd.read_csv(input_file)

# Function to extract average Area (Sqft) from the description
def extract_area_sqft(description):
    if not isinstance(description, str):
        return None
    
    text = description.lower().replace(',', '') # Remove commas for easier regex
    
    # Pattern 1: Look for ranges like "1500 - 2000 sqft" or "1500-2000 sq ft"
    # Looks for digits, optional space, hyphen, optional space, digits, optional space, 'sq'
    range_pattern = r'(\d+)\s*-\s*(\d+)\s*sq'
    range_match = re.search(range_pattern, text)
    
    if range_match:
        val1 = float(range_match.group(1))
        val2 = float(range_match.group(2))
        return (val1 + val2) / 2 # Return average of the range

    # Pattern 2: Look for single values like "1500 sqft"
    single_pattern = r'(\d+)\s*sq'
    single_match = re.search(single_pattern, text)
    
    if single_match:
        return float(single_match.group(1))
        
    return None

# Function to calculate Price Per Sqft
def calc_price_per_sqft(row):
    # Get Price (Use 'Exact_Price' from previous step, or raw 'price' if needed)
    price = row.get('Exact_Price')
    
    # If Exact_Price missing, try to parse the raw 'price' column crudely as backup
    if pd.isna(price) or price == 0:
        return None

    # Get Area
    area = row.get('Extracted_Area_Avg')
    
    # Safety Check: Ensure both price and area exist and Area is not 0
    if pd.notna(price) and pd.notna(area) and area > 0:
        return int(price / area)
    else:
        return None

# --- EXECUTION ---

print("Extracting Area from description...")
# 1. Create a helper column for Area (you can delete this later if you want)
# Make sure 'description' matches your column name exactly
df['Extracted_Area_Avg'] = df['description'].apply(extract_area_sqft)

print("Calculating Price Per Sqft...")
# 2. Calculate Price Per Sqft
df['Price_Per_Sqft'] = df.apply(calc_price_per_sqft, axis=1)

# 3. Save
df.to_csv('my_final_data.csv', index=False, float_format='%.0f')

print("Done! Data saved to 'my_final_data.csv'")
print(df[['price', 'Exact_Price', 'Extracted_Area_Avg', 'Price_Per_Sqft']].head())
