import requests
import json
import urllib3
import time
from config import API_KEY, BASE_URL

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OUTPUT_FILE = "data_records.json"

def fetch_records_all_fields():
    print("🚀 STEP 1: Fetching All Record Variables...")
    
    headers = {"Authorization": f"Token {API_KEY}", "Accept": "application/json"}
    s = requests.Session()
    s.headers.update(headers)

    all_records = []
    page_num = 1
    total_pages = 2 # Will update this from the API response
    
    while page_num <= total_pages:
        print(f"    Fetching Page {page_num} of {total_pages}...", end=" ")
        
        # API Call
        list_url = f"{BASE_URL}/records?page[number]={page_num}&page[size]=50"
        
        try:
            resp = s.get(list_url, verify=False)
            
            if resp.status_code != 200:
                print(f"❌ Error {resp.status_code}")
                break
                
            data = resp.json()
            
            # 1. UPDATE PAGINATION (Use the 'meta' block from your JSON)
            meta = data.get("meta", {})
            # if "totalPages" in meta:
            #     total_pages = meta["totalPages"]
            
            batch = data.get('data', [])
            if not batch:
                print("Done (No data returned).")
                break

            for item in batch:
                attrs = item.get("attributes", {})
                rels = item.get("relationships", {})

                # 2. FLATTEN EVERYTHING
                clean_item = {
                    "id": item.get("id"),
                    "type": item.get("type"),
                    
                    # --- ATTRIBUTES (From your snippet) ---
                    "number": attrs.get("number"),
                    "histID": attrs.get("histID"),
                    "histNumber": attrs.get("histNumber"),
                    "typeDescription": attrs.get("typeDescription"),
                    "status": attrs.get("status"),
                    "isEnabled": attrs.get("isEnabled"),
                    "submittedAt": attrs.get("submittedAt"),
                    "expiresAt": attrs.get("expiresAt"),
                    "renewalOfRecordID": attrs.get("renewalOfRecordID"),
                    "renewalNumber": attrs.get("renewalNumber"),
                    "submittedOnline": attrs.get("submittedOnline"),
                    "renewalSubmitted": attrs.get("renewalSubmitted"),
                    "createdAt": attrs.get("createdAt"),
                    "updatedAt": attrs.get("updatedAt"),
                    "createdBy": attrs.get("createdBy"),
                    "updatedBy": attrs.get("updatedBy"),
                    
                    # --- RELATIONSHIP IDs (Useful for SQL Joins later) ---
                    # We safely check if ['data'] exists before grabbing ['id']
                    "recordTypeId": rels.get("recordType", {}).get("data", {}).get("id"),
                    "projectId": rels.get("project", {}).get("data", {}).get("id")
                }
                
                all_records.append(clean_item)

            print(f"✅ Got {len(batch)} recs. (Total: {len(all_records)})")
            
            page_num += 1
            # Optional: Polite delay to not hammer the server
            # time.sleep(0.2) 

        except Exception as e:
            print(f"\n❌ CRASH: {e}")
            break

    # Save to file
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_records, f, indent=4)
    
    print(f"\n🎉 COMPLETE. Saved {len(all_records)} records to '{OUTPUT_FILE}'")

if __name__ == "__main__":
    fetch_records_all_fields()