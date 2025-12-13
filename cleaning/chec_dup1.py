import pandas as pd

# ==== CONFIG ====
INPUT_FILE = "listings_final.csv"
OUTPUT_FILE = "listings_final1.csv"
# =================

# Load CSV
df = pd.read_csv(INPUT_FILE)

print("Original rows:", len(df))

# Remove duplicates based on 2 columns
df_cleaned = df.drop_duplicates(
    subset=["Google_Maps_Link", "title"],   # <-- both must match
    keep="first"   # keep first occurrence
)

print("After removing duplicates:", len(df_cleaned))
print("Removed:", len(df) - len(df_cleaned))

# Save new file
df_cleaned.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

print("\n✅ DONE")
print("New file saved as:", OUTPUT_FILE)

