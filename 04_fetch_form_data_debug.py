import requests
import json
import urllib3
import os
from config import API_KEY, BASE_URL

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

INPUT_FILE = "data_records_filtered.json"

def debug_deep_form_fetch():
    print("🔍 DEBUG: Performing Deep Fetch to find Form Data...")

    # 1. Load your summary list
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, "r") as f:
        records = json.load(f)

    # 2. Find a valid test record (Skip drafts, they often have no form data)
    target = None
    for r in records:
        if r.get("status") != "DRAFT" and r.get("number"):
            target = r
            break
    
    if not target:
        print("❌ Could not find a valid (non-DRAFT) record to test.")
        return

    sys_id = target["id"]
    permit_num = target["number"]
    print(f"👉 Testing Record: {permit_num} (System ID: {sys_id})")

    headers = {"Authorization": f"Token {API_KEY}", "Accept": "application/json"}
    s = requests.Session()
    s.headers.update(headers)

    # --- STEP 1: GET FULL RECORD DETAILS ---
    print(f"   1. Fetching full details from /records/{sys_id}...")
    detail_url = f"{BASE_URL}/records/{sys_id}"
    
    try:
        resp = s.get(detail_url, verify=False)
        if resp.status_code != 200:
            print(f"❌ Failed to fetch details: {resp.status_code}")
            return
        
        full_record = resp.json().get("data", {})
        
        # --- STEP 2: FIND THE FORM LINK ---
        # Look inside relationships -> formData -> links -> related
        relationships = full_record.get("relationships", {})
        form_rel = relationships.get("formData", {})
        form_url = form_rel.get("links", {}).get("related")

        if not form_url:
            print("❌ This record has no 'formData' link.")
            print("   (It might be an old record or a different type?)")
            return

        print(f"✅ Found Form Data URL: {form_url}")

        # --- STEP 3: FETCH THE ACTUAL FORM DATA ---
        print("   3. Fetching form answers...")
        resp_form = s.get(form_url, verify=False)
        
        if resp_form.status_code == 200:
            form_data = resp_form.json()
            print("\n⬇️  SUCCESS! RAW FORM DATA: ⬇️\n")
            print(json.dumps(form_data, indent=4))
        else:
            print(f"❌ Failed to fetch form data: {resp_form.status_code}")

    except Exception as e:
        print(f"❌ Crash: {e}")

if __name__ == "__main__":
    debug_deep_form_fetch()