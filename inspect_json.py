import json
import os

FILENAME = "opengov_raw_export.json"

print(f"--- INSPECTING V2: {FILENAME} ---")

if not os.path.exists(FILENAME):
    print("❌ File not found.")
    exit()

with open(FILENAME, "r") as f:
    data = json.load(f)

# 1. unwrapping the data if needed
records_list = []

if isinstance(data, list):
    print("✅ Structure: Root is a List.")
    records_list = data
elif isinstance(data, dict) and "data" in data:
    print("✅ Structure: Root is a Dictionary (Found 'data' key).")
    records_list = data["data"]
else:
    print("❌ Unknown structure. Keys found:", list(data.keys()))
    exit()

# 2. Analyze the first record
if len(records_list) > 0:
    first_record = records_list[0]
    print(f"\n✅ Found {len(records_list)} records.")
    print("\n--- SAMPLE RECORD STRUCTURE ---")
    
    # Check top-level keys (id, type, etc.)
    print(f"TOP KEYS: {list(first_record.keys())}")

    # Check the 'attributes' object (where the real data is)
    if "attributes" in first_record:
        print("\n--- ATTRIBUTE FIELDS (These will be your Columns) ---")
        attrs = first_record["attributes"]
        for key, value in attrs.items():
            # Print key and a sample value (truncated) to help identify content
            val_preview = str(value)[:30] 
            print(f"   • {key}: {val_preview}")
    else:
        print("\n❌ No 'attributes' found inside the record.")
else:
    print("⚠️ The list is empty.")

input("\nPress Enter to close...")