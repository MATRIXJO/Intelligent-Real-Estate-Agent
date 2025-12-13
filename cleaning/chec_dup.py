import pandas as pd

FILE = "links.csv"   # your converted csv

df = pd.read_csv(FILE)

# Find duplicated rows
duplicates = df[df.duplicated(keep=False)]

if duplicates.empty:
    print("\n✅ No duplicate rows found!\n")
else:
    print(f"\n❌ {len(duplicates)} duplicate rows found:\n")
    print(duplicates)
    
    # Save duplicates separately
    duplicates.to_csv("duplicates_found.csv", index=False)
    print("\n📁 Duplicates saved to: duplicates_found.csv")

