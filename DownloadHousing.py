import requests
import json
import urllib3
import time
import ssl
import http.client

# --- CONFIGURATION ---
API_KEY = "0ea16721107a2c91af7ea7286c7d6336b0af52ed3d9230e85483110531d1ba88"
COMMUNITY = "springfieldma" 
BASE_URL = f"https://api.plce.opengov.com/plce/v2/{COMMUNITY}"
# HOST = "api.plce.opengov.com"
# PATH = f"/plce/v2/{COMMUNITY}/records?page[number]=1&page[size]=10"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- HELPER: SIMPLIFY THE DATA ---
def extract_clean_data(record_raw, applicant_raw, location_raw, workflow_raw):
    """
    Takes the messy raw JSON parts and builds a clean, simple dictionary.
    """
    attrs = record_raw.get("attributes", {})
    
    # 1. Basic Record Info
    clean_record = {
        "Record_ID": record_raw.get("id"),
        "Permit_Number": attrs.get("number"),
        "Status": attrs.get("status"),
        "Description": attrs.get("typeDescription"),
        "Submitted": attrs.get("submittedAt"),
        "Applicant_Name": "N/A",
        "Applicant_Email": "N/A",
        "Primary_Address": "N/A",
        "Parcel_Number": "N/A",
        "Workflow_Steps": []
    }

    # 2. Extract Applicant Info
    if applicant_raw:
        app_attrs = applicant_raw.get("attributes", {})
        fname = app_attrs.get("firstName", "")
        lname = app_attrs.get("lastName", "")
        full_name = f"{fname} {lname}".strip() or app_attrs.get("name")
        
        clean_record["Applicant_Name"] = full_name
        clean_record["Applicant_Email"] = app_attrs.get("email")

    # 3. Extract Location Info
    if location_raw:
        loc_attrs = location_raw.get("attributes", {})
        clean_record["Primary_Address"] = loc_attrs.get("fullAddress")
        clean_record["Parcel_Number"] = loc_attrs.get("parcelNumber")

    # 4. Extract Workflow Summary (With Filter)
    if workflow_raw:
        for step in workflow_raw:
            step_attrs = step.get("attributes", {})
            step_name = step_attrs.get("label")
            
            # --- THE FILTER ---
            # If name is None or Empty String, skip this step entirely
            if not step_name: 
                continue

            clean_record["Workflow_Steps"].append({
                "Step_Name": step_name,
                "Step_Status": step_attrs.get("status"),
                "Completed_Date": step_attrs.get("completedAt"),
                "Assigned_To": step_attrs.get("assignedUserName")
            })

    return clean_record

# --- MAIN PROCESS ---
def fetch_and_organize():
    print(f"🚀 Starting clean fetch for {COMMUNITY}...")
    
    headers = {"Authorization": f"Token {API_KEY}", "Accept": "application/json"}
    s = requests.Session()
    s.headers.update(headers)

    raw_source_list = []      
    clean_summary_list = []   

    page_num = 1
    page_size = 10 
    keep_fetching = True

    while keep_fetching:
        print(f"\n📄 Processing Page {page_num}...")
        
        # 1. FETCH RAW LIST
        list_url = f"{BASE_URL}/records?page[number]={page_num}&page[size]={page_size}"
        req = requests.Request('GET', list_url, headers=headers)
        prepped = s.prepare_request(req)
        prepped.url = list_url 
        
        try:
            resp = s.send(prepped, verify=False)
            if resp.status_code != 200:
                print(f"❌ Error {resp.status_code}")
                break
            
            data = resp.json()
            records_batch = data.get('data', [])
            
            if not records_batch:
                print("No more records.")
                break

            # STORE RAW DATA 
            raw_source_list.extend(records_batch)

            # 2. FETCH DETAILS & SIMPLIFY
            print(f"   Fetching details for {len(records_batch)} records...")
            
            for record in records_batch:
                rid = record.get("id")
                
                # Fetch details
                app_resp = s.get(f"{BASE_URL}/records/{rid}/applicant", verify=False)
                app_data = app_resp.json().get('data') if app_resp.status_code == 200 else None

                loc_resp = s.get(f"{BASE_URL}/records/{rid}/primary-location", verify=False)
                loc_data = loc_resp.json().get('data') if loc_resp.status_code == 200 else None

                wf_resp = s.get(f"{BASE_URL}/records/{rid}/workflow-steps", verify=False)
                wf_data = wf_resp.json().get('data', []) if wf_resp.status_code == 200 else []

                # Create the clean object
                clean_obj = extract_clean_data(record, app_data, loc_data, wf_data)
                clean_summary_list.append(clean_obj)
                
                print(".", end="", flush=True)

            page_num += 1
            if page_num > 1: 
                keep_fetching = False

        except Exception as e:
            print(f"\n❌ CRASH: {e}")
            break

    # --- SAVE FILES ---
    print("\n\n💾 Saving Output Files...")

    with open("1_raw_source.json", "w") as f:
        json.dump(raw_source_list, f, indent=4)
    print(f"✅ Saved '1_raw_source.json'")

    with open("2_clean_summary.json", "w") as f:
        json.dump(clean_summary_list, f, indent=4)
    print(f"✅ Saved '2_clean_summary.json'")

if __name__ == "__main__":
    fetch_and_organize()