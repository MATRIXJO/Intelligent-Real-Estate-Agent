import pandas as pd
import re
import urllib.parse

# 1. Load your file
df = pd.read_csv('my_listings_final_complete.csv')

# ==========================================
# EXPANDED MASTER DATA
# ==========================================
locality_database = {
    # --- NORTH ---
    'Devanahalli': 'North', 'Yelahanka': 'North', 'Hebbal': 'North', 
    'Thanisandra': 'North', 'Jakkur': 'North', 'Bagalur': 'North', 
    'Hennur': 'North', 'Sahakara Nagar': 'North', 'Vidyaranyapura': 'North', 
    'RT Nagar': 'North', 'Peenya': 'North', 'Yeshwanthpur': 'North', 
    'Jalahalli': 'North', 'Mathikere': 'North', 'Sanjay Nagar': 'North', 
    'Nagawara': 'North', 'Kogilu': 'North', 'Doddaballapur': 'North', 
    'Chikkajala': 'North', 'Kalyan Nagar': 'North', 'HRBR Layout': 'North', 
    'HBR Layout': 'North', 'Banaswadi': 'North', 'Horamavu': 'North', 
    'Kothanur': 'North', 'Hessarghatta': 'North', 'Nelamangala': 'North',
    'Manyata Tech Park': 'North', 'Nandi Hills': 'North', 'Bel Road': 'North',
    'Chikkaballapur': 'North', 'Tindlu': 'North', 'Kodigehalli': 'North',
    'Bettahalsoor': 'North', 'Huttanahalli': 'North', 'Sreeramanahalli': 'North',
    'Tumkur Road': 'North', 'Tumkuru Road': 'North', 'Doddaballapura': 'North',
    'Jalige': 'North', 'Budihals': 'North',

    # --- EAST ---
    'Whitefield': 'East', 'Sarjapur': 'East', 'Varthur': 'East', 
    'Marathahalli': 'East', 'KR Puram': 'East', 'Mahadevapura': 'East', 
    'Bellandur': 'East', 'Brookefield': 'East', 'Kundalahalli': 'East', 
    'Hoodi': 'East', 'Budigere': 'East', 'Hoskote': 'East', 
    'Old Madras Road': 'East', 'Old Airport Road': 'East', 'CV Raman Nagar': 'East', 
    'Kaggadasapura': 'East', 'Kadugodi': 'East', 'Panathur': 'East', 
    'Gunjur': 'East', 'Ramamurthy Nagar': 'East', 'Kasturi Nagar': 'East', 
    'ITPL': 'East', 'AECS Layout': 'East', 'BEML Layout': 'East',
    'Bidarahalli': 'East', 'Seegehalli': 'East', 'Thubarahalli': 'East',
    'Munnekollal': 'East', 'Vignan Nagar': 'East', 'Domlur': 'East', 
    'Indiranagar': 'East', 'Aavalahalli': 'East', 'TC Palaya': 'East',
    'Kithaganur': 'East', 'Belathur': 'East', 'Medahalli': 'East',
    'Sadaramangala': 'East', 'Bhattarahalli': 'East', 'Cheemasandra': 'East',
    'Chikkanahalli': 'East', 'Doddabanahalli': 'East', 'Sonnenahalli': 'East',
    'Ayyappa Nagar': 'East', 'Konadasapura': 'East', 'Kannamangala': 'East',
    'Katamnallur': 'East', 'Hirandahalli': 'East', 'Battarahalli': 'East',
    'Soukya Road': 'East', 'Nallurhalli': 'East', 'Pattandur Agrahara': 'East',
    'Channasandra': 'East', 'Garudachar Palya': 'East', 'Mugalur': 'East',
    'Kambalipura': 'East', 'Siddapura': 'East', 'Dodda Nekkundi': 'East',
    'Bommenahalli': 'East', 'Chikka Tirupathi': 'East', 'Kodihalli': 'East',
    'Avalahalli': 'East', 'Huskur': 'East',

    # --- SOUTH ---
    'Electronic City Phase 1': 'South', 'Electronic City Phase 2': 'South',
    'Electronics City Phase 1': 'South', 'Electronics City Phase 2': 'South',
    'Electronic City': 'South', 'Electronics City': 'South', 'E-City': 'South',
    'Koramangala': 'South', 'HSR Layout': 'South', 'BTM Layout': 'South', 
    'Jayanagar': 'South', 'JP Nagar': 'South', 'Bannerghatta': 'South', 
    'Kanakapura': 'South', 'Hosur Road': 'South', 'Begur': 'South', 
    'Bommanahalli': 'South', 'Basavanagudi': 'South', 'Padmanabhanagar': 'South', 
    'Kumaraswamy Layout': 'South', 'Uttarahalli': 'South', 'Banashankari': 'South', 
    'Arekere': 'South', 'Hulimavu': 'South', 'Gottigere': 'South', 
    'Jigani': 'South', 'Anekal': 'South', 'Attibele': 'South', 
    'Chandapura': 'South', 'Harlur': 'South', 'Kudlu': 'South', 
    'Singasandra': 'South', 'Konanakunte': 'South', 'Billekahalli': 'South', 
    'Ejipura': 'South', 'Tavarekere': 'South', 'Anjanapura': 'South', 
    'Mylasandra': 'South', 'Kammasandra': 'South', 'Naganathapura': 'South', 
    'Yadavanahalli': 'South', 'Talaghattapura': 'South', 'Subramanyapura': 'South', 
    'Doddakallasandra': 'South', 'Vajarahalli': 'South', 'Ramanjaneyanagar': 'South', 
    'Kaggalipura': 'South', 'Harohalli': 'South', 'Chikkalasandra': 'South', 
    'Nobel Residency': 'South', 'Narayana Nagar': 'South', 'Gollahalli': 'South', 
    'Hullahalli': 'South', 'Hosa Road': 'South', 'Bommasandra': 'South',
    'Bomasandra': 'South', 'Kachamaranahalli': 'South', 'Kachanayakanahalli': 'South',
    'Yarandahalli': 'South', 'Huskur': 'South', 'Hebbagodi': 'South',

    # --- WEST ---
    'Malleshwaram': 'West', 'Rajajinagar': 'West', 'Vijayanagar': 'West', 
    'Basaveshwara Nagar': 'West', 'Nagarbhavi': 'West', 'Kengeri': 'West', 
    'Mysore Road': 'West', 'Magadi Road': 'West', 'Chandra Layout': 'West', 
    'Mahalakshmi Layout': 'West', 'Nandini Layout': 'West', 'RR Nagar': 'West', 
    'Rajarajeshwari Nagar': 'West', 'Kumbalgodu': 'West', 'Bidadi': 'West', 
    'Nayandahalli': 'West', 'Chikkabidarakallu': 'West', 
    'Nagasandra': 'West', 'Dasarahalli': 'West', 'Jnana Jyothi Nagar': 'West',
    'Ramasandra': 'West', 'Kommaghatta': 'West', 'Doddabele': 'West',
    'Srirampuram': 'West', 'Tavarekere': 'West',

    # --- CENTRAL ---
    'MG Road': 'Central', 'Brigade Road': 'Central', 'Cunningham Road': 'Central', 
    'Lavelle Road': 'Central', 'Richmond Road': 'Central', 'Vasanth Nagar': 'Central', 
    'Shivajinagar': 'Central', 'Frazer Town': 'Central', 'Benson Town': 'Central', 
    'Ulsoor': 'Central', 'Halasuru': 'Central', 'Shanthi Nagar': 'Central', 
    'Wilson Garden': 'Central', 'Seshadripuram': 'Central', 'Majestic': 'Central', 
    'Chamarajpet': 'Central', 'Cubbonpet': 'Central', 'Chickpet': 'Central',
    'Ashok Nagar': 'Central', 'Sudhama Nagar': 'Central', 'Sampangiram Nagar': 'Central'
}

# Sort keys by length (Longest first) to prioritize specific matches
# e.g. Match "Electronics City Phase 1" before "Electronics City"
sorted_localities = sorted(locality_database.keys(), key=len, reverse=True)

# ==========================================
# EXTRACTION LOGIC
# ==========================================

def process_row(row):
    # 1. Prepare text sources
    title_text = str(row['title']).lower()
    location_text = str(row['location']).lower()
    desc_text = str(row['description']).lower()
    map_link = str(row.get('Google_Maps_Link', '')).lower()

    # Combine priority text (Title + Location)
    primary_text = f"{title_text} {location_text}"
    primary_text = re.sub(r'[^\w\s]', ' ', primary_text) # Clean punctuation

    # Search in Title + Location first
    for loc in sorted_localities:
        # Use word boundary \b to avoid partial matches (e.g. 'Male' inside 'Maleshwaram')
        pattern = r'\b' + re.escape(loc.lower()) + r'\b'
        if re.search(pattern, primary_text):
            return pd.Series([loc, locality_database[loc]])

    # 2. If not found, check Google Maps Link (often has cleaner query params)
    if 'query=' in map_link:
        try:
            query_part = map_link.split('query=')[1].split('&')[0]
            decoded_text = urllib.parse.unquote_plus(query_part).lower()
            
            for loc in sorted_localities:
                pattern = r'\b' + re.escape(loc.lower()) + r'\b'
                if re.search(pattern, decoded_text):
                    return pd.Series([loc, locality_database[loc]])
        except:
            pass

    # 3. Last Resort: Check Description
    # (Less reliable but useful for empty titles)
    desc_text = re.sub(r'[^\w\s]', ' ', desc_text)
    for loc in sorted_localities:
        pattern = r'\b' + re.escape(loc.lower()) + r'\b'
        if re.search(pattern, desc_text):
            return pd.Series([loc, locality_database[loc]])

    return pd.Series([None, None])

# Apply the function
df[['Extracted_Locality', 'Zone']] = df.apply(process_row, axis=1)

# ==========================================
# SAVE
# ==========================================
df.to_csv('my_listings_zoned_v3.csv', index=False)

print("Extraction complete.")
print(f"Rows filled: {df['Extracted_Locality'].notna().sum()} out of {len(df)}")
# Show a sample of the problematic ones to verify they are fixed
check_list = ['hosa road', 'tumkur', 'bommasandra', 'electronic city']
mask = df['title'].str.lower().str.contains('|'.join(check_list))
print(df[mask][['title', 'Extracted_Locality', 'Zone']].head(10))
