import requests
import json
import urllib3
from config import API_KEY, BASE_URL

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# We know this from your previous JSON output
TEST_RECORD_ID = "708708"
RECORD_TYPE_ID = "1006586" 

def fix_and_fetch_form():
    print(f"🔍 DIAGNOSTIC: Finding the correct Form ID for Record Type {RECORD_TYPE_ID}...")

    headers = {"Authorization": f"Token {API_KEY}", "Accept": "application/json"}
    s = requests.Session()
    s.headers.update(headers)

    # 1. Fetch Record Type Details to find the "Form Definition"
    # This tells us which "name" ID is required
    type_url = f"{BASE_URL}/record-types/{RECORD_TYPE_ID}"
    
    try:
        print(f"   Fetching Record Type info...")
        resp = s.get(type_url, verify=False)
        
        if resp.status_code != 200:
            print(f"❌ Failed to fetch Record Type: {resp.status_code}")
            return
            
        type_data = resp.json().get("data", {})
        
        # 2. Look for the Form Definition Link
        # Usually in relationships -> formDefinitions -> links -> related
        form_rel = type_data.get("relationships", {}).get("formDefinitions", {})
        related_link = form_rel.get("links", {}).get("related")
        
        if not related_link:
            print("❌ Could not find a link to Form Definitions in the Record Type.")
            return
            
        print(f"   Fetching Form Definitions list from: {related_link}")
        
        # 3. Fetch the list of forms
        resp_forms = s.get(related_link, verify=False)
        forms_list = resp_forms.json().get("data", [])
        
        if not forms_list:
            print("❌ No forms found attached to this Record Type.")
            return
            
        # We usually take the first one, or look for one that is "active"
        target_form = forms_list[0]
        form_def_id = target_form.get("id")
        form_name = target_form.get("attributes", {}).get("name")
        
        print(f"✅ FOUND FORM DEFINITION: '{form_name}' (ID: {form_def_id})")
        
        # --- STEP 4: RETRY THE FETCH WITH THE ID ---
        print(f"\n🚀 Retrying Record {TEST_RECORD_ID} with ?name={form_def_id}...")
        
        final_url = f"{BASE_URL}/records/{TEST_RECORD_ID}/form?name={form_def_id}"
        print(f"   URL: {final_url}")
        
        resp_final = s.get(final_url, verify=False)
        
        if resp_final.status_code == 200:
            data = resp_final.json()
            print("\n⬇️  SUCCESS! WE CRACKED IT! ⬇️\n")
            print(json.dumps(data, indent=4))
        else:
            print(f"❌ Still failed: {resp_final.status_code}")
            print(resp_final.text)

    except Exception as e:
        print(f"❌ Crash: {e}")

if __name__ == "__main__":
    fix_and_fetch_form()