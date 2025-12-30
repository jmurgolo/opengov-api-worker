import requests
import json
import urllib3
from config import API_KEY, BASE_URL

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# CONFIG
TEST_RECORD_ID = "708708" 
# The weird ID you found
RAW_ID = "migration)-0197a858-8749-78f3-a7c2-f38cb20a2812"
# The "Clean" version (stripped of the weird prefix)
CLEAN_UUID = "0197a858-8749-78f3-a7c2-f38cb20a2812"

def brute_force_search():
    print(f"🔨 STARTING BRUTE FORCE SEARCH ON RECORD {TEST_RECORD_ID}...")
    
    headers = {"Authorization": f"Token {API_KEY}", "Accept": "application/json"}
    s = requests.Session()
    s.headers.update(headers)

    # --- ATTEMPT 1: The "Clean" UUID ---
    print(f"\n1️⃣  Testing 'Clean' UUID: {CLEAN_UUID}...")
    url = f"{BASE_URL}/records/{TEST_RECORD_ID}/form?name={CLEAN_UUID}&include=sections"
    try:
        resp = s.get(url, verify=False)
        if resp.status_code == 200:
            print("✅ SUCCESS! The prefix was the problem!")
            print(json.dumps(resp.json(), indent=4)[:500])
            return
        else:
            print(f"❌ Failed ({resp.status_code})")
    except: pass

    # --- ATTEMPT 2: The /intake-form Endpoint (No ID needed) ---
    # This is often the backup location for migrated records
    print(f"\n2️⃣  Testing '/intake-form' endpoint...")
    url = f"{BASE_URL}/records/{TEST_RECORD_ID}/intake-form?include=sections"
    try:
        resp = s.get(url, verify=False)
        if resp.status_code == 200:
            print("✅ SUCCESS! Found data at /intake-form!")
            data = resp.json()
            # Check if it actually has answers
            if data.get("included"):
                print(f"   Found {len(data['included'])} fields!")
                print(json.dumps(data, indent=4)[:500])
                return
            else:
                print("   (Response 200, but no 'included' data found)")
        else:
            print(f"❌ Failed ({resp.status_code})")
    except: pass

    # --- ATTEMPT 3: The /forms (Plural) Endpoint ---
    # Sometimes you can ask "What forms does this record have?"
    print(f"\n3️⃣  Testing '/forms' list...")
    url = f"{BASE_URL}/records/{TEST_RECORD_ID}/forms"
    try:
        resp = s.get(url, verify=False)
        if resp.status_code == 200:
            print("✅ SUCCESS! Found a form list!")
            print(json.dumps(resp.json(), indent=4))
        else:
            print(f"❌ Failed ({resp.status_code})")
    except: pass

    print("\n🏁 Search complete.")

if __name__ == "__main__":
    brute_force_search()
