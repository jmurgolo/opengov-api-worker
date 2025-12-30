import requests
import json
import urllib3
from config import API_KEY, BASE_URL

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Config
RECORD_TYPE_ID = "1006586"  # Housing Enforcement
TEST_RECORD_ID = "708708"   # The record we are trying to read

def fetch_form_data_chain():
    print("🚀 STARTING CHAIN REACTION TO FIND FORM DATA...")
    
    headers = {"Authorization": f"Token {API_KEY}", "Accept": "application/json"}
    s = requests.Session()
    s.headers.update(headers)

    # --- STEP 1: Get Record Type to find the Form Definition Link ---
    print(f"\n1️⃣  Inspecting Record Type {RECORD_TYPE_ID}...")
    type_url = f"{BASE_URL}/record-types/{RECORD_TYPE_ID}"
    resp_type = s.get(type_url, verify=False)
    
    if resp_type.status_code != 200:
        print(f"❌ Failed to get record type: {resp_type.status_code}")
        return

    json_data = resp_type.json().get("data")

    # SAFETY CHECK: Handle if it returns a List [{},{}] or a Dict {}
    if isinstance(json_data, list):
        if len(json_data) > 0:
            type_data = json_data[0]
        else:
            print("❌ API returned an empty data list.")
            return
    elif isinstance(json_data, dict):
        type_data = json_data
    else:
        print(f"❌ Unexpected data format: {type(json_data)}")
        return
    
    # Grab the link from 'formFields' -> 'links' -> 'related'
    try:
        form_meta_url = type_data["relationships"]["formFields"]["links"]["related"]
        print(f"✅ Found Form Definition URL: {form_meta_url}")
    except KeyError:
        print("❌ Could not find 'formFields' relationship link.")
        print("   Available keys:", type_data.get("relationships", {}).keys())
        return

    # --- STEP 2: Fetch that URL to get the Form ID ---
    print(f"\n2️⃣  Fetching Form ID from definition...")
    resp_meta = s.get(form_meta_url, verify=False)
    
    if resp_meta.status_code != 200:
        print(f"❌ Failed to get form definition: {resp_meta.status_code}")
        return

    # The ID of this object is the 'name=' parameter we need!
    meta_data = resp_meta.json().get("data", {})
    
    # Handle list vs dict again just to be safe
    if isinstance(meta_data, list) and len(meta_data) > 0:
        meta_data = meta_data[0]
        
    form_def_id = meta_data.get("id")
    
    if not form_def_id:
        print("❌ API returned data, but no ID found in 'data'.")
        print(json.dumps(meta_data, indent=4))
        return

    print(f"🔑 CRACKED IT! Form Definition ID is: {form_def_id}")

    # --- STEP 3: Fetch the ACTUAL Record Data using the ID ---
    print(f"\n3️⃣  Fetching Record Answers using ?name={form_def_id}...")
    
    # We construct the URL manually now that we have the key
    final_url = f"{BASE_URL}/records/{TEST_RECORD_ID}/form?name={form_def_id}&include=sections"
    
    print(f"👉 URL: {final_url}")
    
    resp_final