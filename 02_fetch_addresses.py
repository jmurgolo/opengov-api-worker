import requests
import json
import urllib3
import os
import time
from config import API_KEY, BASE_URL

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

INPUT_FILE = "data_records.json"       
OUTPUT_FILE = "data_addresses.json"     
ERROR_FILE = "data_address_errors.json" 

MAX_RETRIES = 5  

def fetch_addresses_with_retry_loop():
    print("🚀 STEP 2: Fetching Address Details (Smart Retry Mode)...")

    # 1. LOAD MASTER RECORDS
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: '{INPUT_FILE}' not found. Run Step 1 first.")
        return

    with open(INPUT_FILE, "r") as f:
        all_records = json.load(f)

    headers = {"Authorization": f"Token {API_KEY}", "Accept": "application/json"}
    s = requests.Session()
    s.headers.update(headers)

    attempt = 1
    
    while attempt <= MAX_RETRIES:
        # 2. RELOAD COMPLETED LIST (Robust Load)
        processed_ids = set()
        if os.path.exists(OUTPUT_FILE):
            try:
                # Check if file has content before loading
                if os.path.getsize(OUTPUT_FILE) > 0:
                    with open(OUTPUT_FILE, "r") as f:
                        existing = json.load(f)
                        for item in existing:
                            processed_ids.add(item["record_id"])
                else:
                    print("⚠️ Output file is empty. Starting fresh.")
            except json.JSONDecodeError:
                print("⚠️ Output file corrupted. Starting fresh.")
                processed_ids = set()

        # 3. BUILD QUEUE
        queue = []
        for r in all_records:
            if r["id"] in processed_ids: continue
            if r.get("status") == "DRAFT" or not r.get("number"): continue
            queue.append(r)

        if not queue:
            print("\n🎉 SUCCESS! Queue is empty. All valid records have addresses.")
            if os.path.exists(ERROR_FILE):
                try: os.remove(ERROR_FILE)
                except: pass
            break

        print(f"\n📋 ATTEMPT {attempt}/{MAX_RETRIES}: Processing {len(queue)} records...")
        
        current_batch_successes = []
        current_batch_errors = []

        # Process Queue
        for i, rec in enumerate(queue):
            # Polite pause
            time.sleep(0.4) 

            record_id = rec.get("id")
            permit_number = rec.get("number")
            url = f"{BASE_URL}/records/{record_id}/primary-location"
            
            try:
                resp = s.get(url, verify=False)
                
                # CASE 1: SUCCESS (200)
                if resp.status_code == 200:
                    loc_wrapper = resp.json().get('data')
                    
                    if loc_wrapper:
                        attrs = loc_wrapper.get('attributes', {})
                        
                        street_num = attrs.get("streetNo") or attrs.get("streetNumber")
                        street_name = attrs.get("streetName")
                        
                        full_addr = attrs.get("fullAddress")
                        if not full_addr and street_num and street_name:
                            full_addr = f"{street_num} {street_name}"

                        address_entry = {
                            "record_id": record_id,       
                            "permit_number": permit_number, 
                            "location_id": loc_wrapper.get("id"),
                            "full_address": full_addr,
                            "street_no": street_num,
                            "street_name": street_name,
                            "unit": attrs.get("unit"),
                            "city": attrs.get("city"),
                            "state": attrs.get("state"),
                            "zip": attrs.get("postalCode"),
                            "country": attrs.get("country"),
                            "mbl": attrs.get("mbl"),
                            "latitude": attrs.get("latitude"),
                            "longitude": attrs.get("longitude"),
                            "location_type": attrs.get("locationType"),
                            "owner_name": attrs.get("ownerName"),
                            "owner_street_no": attrs.get("ownerStreetNumber"),
                            "owner_street_name": attrs.get("ownerStreetName"),
                            "owner_unit": attrs.get("ownerUnit"),
                            "owner_city": attrs.get("ownerCity"),
                            "owner_state": attrs.get("ownerState"),
                            "owner_zip": attrs.get("ownerPostalCode"),
                            "owner_country": attrs.get("ownerCountry"),
                            "owner_phone": attrs.get("ownerPhoneNo"),
                            "owner_email": attrs.get("ownerEmail"),
                            "lot_area": attrs.get("lotArea"),
                            "occupancy_type": attrs.get("occupancyType"),
                            "property_use": attrs.get("propertyUse"),
                            "sewage": attrs.get("sewage"),
                            "water": attrs.get("water"),
                            "year_built": attrs.get("yearBuilt"),
                            "zoning": attrs.get("zoning"),
                            "building_type": attrs.get("buildingType")
                        }
                        current_batch_successes.append(address_entry)
                        print("✅", end="", flush=True)

                    else:
                        print("o", end="", flush=True) # Valid but empty

                # CASE 2: NOT FOUND (404)
                elif resp.status_code == 404:
                    print("-", end="", flush=True)

                # CASE 3: SERVER ERROR (500) -> PAUSE!
                elif resp.status_code >= 500:
                    print(f"x({resp.status_code})", end="", flush=True)
                    current_batch_errors.append(rec)
                    # Cool down for 5 seconds if server is struggling
                    time.sleep(5) 

                # CASE 4: OTHER ERRORS
                else:
                    print(f"x({resp.status_code})", end="", flush=True)
                    current_batch_errors.append(rec)

            except Exception as e:
                print("!", end="", flush=True)
                current_batch_errors.append(rec)

        # 4. SAVE PROGRESS SAFELY
        if current_batch_successes:
            existing_data = []
            if os.path.exists(OUTPUT_FILE):
                try:
                    if os.path.getsize(OUTPUT_FILE) > 0:
                        with open(OUTPUT_FILE, "r") as f:
                            existing_data = json.load(f)
                except:
                    existing_data = [] # If corrupt, overwrite
            
            existing_data.extend(current_batch_successes)
            
            with open(OUTPUT_FILE, "w") as f:
                json.dump(existing_data, f, indent=4)
            print(f"\n   💾 Saved {len(current_batch_successes)} new addresses.")

        # 5. RETRY LOGIC
        if current_batch_errors:
            print(f"\n   ⚠️ Attempt {attempt} failed for {len(current_batch_errors)} records.")
            
            with open(ERROR_FILE, "w") as f:
                json.dump(current_batch_errors, f, indent=4)
            
            attempt += 1
            if attempt <= MAX_RETRIES:
                print(f"   ⏳ Waiting 10 seconds before retrying...")
                time.sleep(10)
            else:
                print("   ❌ Max retries reached.")
        else:
            print("\n   ✅ Batch complete with ZERO errors.")
            if os.path.exists(ERROR_FILE):
                try: os.remove(ERROR_FILE)
                except: pass
            break

if __name__ == "__main__":
    fetch_addresses_with_retry_loop()