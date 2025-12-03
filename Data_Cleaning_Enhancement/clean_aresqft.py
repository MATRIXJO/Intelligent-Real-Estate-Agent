import pandas as pd
import numpy as np

# 1. Load your file (the one updated from the previous steps)
df = pd.read_csv('my_updated.csv')

# 2. Ensure the columns are treated as numbers (just to be safe)
df['Exact_Price'] = pd.to_numeric(df['Exact_Price'], errors='coerce')
df['Cleaned_Area'] = pd.to_numeric(df['Cleaned_Area'], errors='coerce')

# 3. Calculate Price Per Sqft
# Logic: Total Price / Total Area
df['Price_Per_Sqft'] = df['Exact_Price'] / df['Cleaned_Area']

# 4. Cleanup
# Replace infinity values (caused if Area is 0) with Empty/NaN
df['Price_Per_Sqft'] = df['Price_Per_Sqft'].replace([np.inf, -np.inf], np.nan)

# Round to the nearest whole number (e.g., 5432.8 -> 5433)
df['Price_Per_Sqft'] = df['Price_Per_Sqft'].round(0)

# 5. Save the final file
df.to_csv('my_final_listings.csv', index=False)

print("Calculation complete. Saved to 'my_final_listings.csv'")
print(df[['Exact_Price', 'Cleaned_Area', 'Price_Per_Sqft']].head())
