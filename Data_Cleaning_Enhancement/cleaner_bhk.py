import pandas as pd
import re

# 1. Load your CSV file
# Replace 'my.csv' with the actual name of your file if different
df = pd.read_csv('my_updated_exact.csv')

# Function to extract numbers only if the row is about an Apartment/Villa
def extract_bhk_counts(text):
    # Convert to string and lower case for safety
    text = str(text)
    
    # Check if 'Land' or 'Plot' is in the text (Skip these)
    if 'Land' in text or 'Plot' in text:
        return []
    
    # Regex to find all numbers (digits) in the string
    # This handles "2, 3 BHK" as well as "4 BHK"
    numbers = re.findall(r'\d+', text)
    
    # Convert the strings found to integers
    return [int(num) for num in numbers]

# 2. Apply the function to your column
# IMPORTANT: Replace 'Property_Type' below with the actual name of the column in your CSV
# (The column shown in your screenshot)
column_name = 'property_type' 

# Create the new column
df['BHK_List'] = df[column_name].apply(extract_bhk_counts)

# 3. Save the updated file
df.to_csv('my_updated.csv', index=False)

print("Extraction complete. Data saved to 'my_updated.csv'")
print(df[[column_name, 'BHK_List']].head())
