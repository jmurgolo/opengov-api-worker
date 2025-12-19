import requests
import json
import urllib3
import os
from config import API_KEY, BASE_URL

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_addresses_final():
    print("🚀 STEP 2: Fetching Address Details...")

    if not os.path.exists("data_records.json"):
        print("❌ Error: 'data_records.json' not found.")
        return

    with open("data_records.json", "r") as f:
        records = json.load(f)

    print(f"   Processing {len(records)} records...")

    headers = {"Authorization": f"Token {API_KEY}", "Accept": "application/json"}
    s = requests.Session()
    s.headers.update(headers)

    address_data = []

    for i, rec in enumerate(records):
        record_id = rec.get("id")
        
        # This is the ONLY valid endpoint according to your inspection
        url = f"{BASE_URL}/records/{record_id}/primary-location"
        
        row = {
            "Record_ID": record_id,
            "Full_Address": None,
            "Street_No": None,
            "Street_Name": None,
            "City": None,
            "State": None,
            "Zip": None,
            "MBL": None
        }

        try:
            resp = s.get(url, verify=False)
            
            # CASE 1: Success (200 OK) - We found an address
            if resp.status_code == 200:
                loc_data = resp.json().get('data')
                
                if loc_data:
                    attrs = loc_data.get('attributes', {})
                    
                    # Map the fields (using the schema you provided earlier)
                    row["Street_No"] = attrs.get("streetNo")
                    row["Street_Name"] = attrs.get("streetName")
                    row["City"] = attrs.get("city")
                    row["State"] = attrs.get("state")
                    row["Zip"] = attrs.get("postalCode")
                    row["MBL"] = attrs.get("mbl")
                    
                    # Create a readable Full Address
                    if row["Street_No"] and row["Street_Name"]:
                        row["Full_Address"] = f"{row['Street_No']} {row['Street_Name']}, {row['City']}"
                    
                    print("✅", end="", flush=True) # Found
                else:
                    print("o", end="", flush=True) # 200 OK, but empty data
            
            # CASE 2: Valid "Empty" (404 Not Found)
            # This is NOT an error. It just means the permit has no location.
            elif resp.status_code == 404:
                print("-", end="", flush=True) # "Dash" means no address exists
            
            # CASE 3: Actual Error
            else:
                print("x", end="", flush=True) # Server error

            address_data.append(row)

        except Exception as e:
            print("!", end="", flush=True)

    # Save Results
    print(f"\n\n💾 Saving {len(address_data)} addresses...")
    with open("data_addresses.json", "w") as f:
        json.dump(address_data, f, indent=4)
    print("✅ Done! Check 'data_addresses.json'.")

if __name__ == "__main__":
    fetch_addresses_final()