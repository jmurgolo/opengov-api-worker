import requests
import json
import urllib3
import os
import time
from config import API_KEY, BASE_URL

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_addresses():
    print("🚀 STEP 2: Fetching Address Details...")

    # 1. Load the list we downloaded in Step 1
    if not os.path.exists("data_records.json"):
        print("❌ Error: 'data_records.json' not found. Run Step 1 first.")
        return

    with open("data_records.json", "r") as f:
        records = json.load(f)

    print(f"   Found {len(records)} records to process.")

    headers = {"Authorization": f"Token {API_KEY}", "Accept": "application/json"}
    s = requests.Session()
    s.headers.update(headers)

    address_data = []

    # 2. Loop through and fetch location for each ID
    for i, rec in enumerate(records):
        record_id = rec.get("id")
        
        # Endpoint: /records/:id/primary-location
        url = f"{BASE_URL}/records/{record_id}/primary-location"
        
        try:
            resp = s.get(url, verify=False)
            
            # Prepare the row
            row = {
                "Record_ID": record_id, # Foreign Key to join back to main table
                "Full_Address": None,
                "Parcel_Number": None,
                "Street_No": None,
                "Street_Name": None
            }

            if resp.status_code == 200:
                loc_raw = resp.json().get('data')
                if loc_raw:
                    attrs = loc_raw.get('attributes', {})
                    row["Full_Address"] = attrs.get("fullAddress")
                    row["Parcel_Number"] = attrs.get("parcelNumber")
                    row["Street_No"] = attrs.get("streetNumber")
                    row["Street_Name"] = attrs.get("streetName")
                    print(".", end="", flush=True)
                else:
                    print("o", end="", flush=True) # "o" means empty location
            else:
                print("x", end="", flush=True) # "x" means error

            address_data.append(row)

        except Exception as e:
            print(f"!")

    # 3. Save the Address Table
    print(f"\n\n💾 Saving {len(address_data)} addresses...")
    with open("data_addresses.json", "w") as f:
        json.dump(address_data, f, indent=4)
    print("✅ Done! You now have 'data_records.json' and 'data_addresses.json'.")

if __name__ == "__main__":
    fetch_addresses()