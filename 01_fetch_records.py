import requests
import json
import urllib3
import time
from config import API_KEY, BASE_URL

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_records_with_numbers():
    print("🚀 STEP 1: Fetching Records (Flattens Data)...")
    
    headers = {"Authorization": f"Token {API_KEY}", "Accept": "application/json"}
    s = requests.Session()
    s.headers.update(headers)

    all_records = []
    page_num = 1
    page_size = 50 
    keep_fetching = True

    while keep_fetching:
        print(f"    Fetching Page {page_num}...", end=" ")
        
        list_url = f"{BASE_URL}/records?page[number]={page_num}&page[size]={page_size}"
        
        try:
            req = requests.Request('GET', list_url, headers=headers)
            prepped = s.prepare_request(req)
            prepped.url = list_url 
            
            resp = s.send(prepped, verify=False)
            
            if resp.status_code != 200:
                print(f"❌ Error {resp.status_code}")
                break
                
            data = resp.json()
            batch = data.get('data', [])

            if not batch:
                print("Done.")
                break

            for item in batch:
                attrs = item.get("attributes", {})
                
                # --- FLATTENED STRUCTURE (No nested 'attributes') ---
                clean_item = {
                    "id": item.get("id"),
                    "type": item.get("type"),
                    # Pull fields directly to the top level
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
                    "updatedBy": attrs.get("updatedBy")
                }
                all_records.append(clean_item)

            print(f"Got {len(batch)}. Total: {len(all_records)}")
            
            page_num += 1
            if page_num > 10: keep_fetching = False 

        except Exception as e:
            print(f"\n❌ CRASH: {e}")
            break

    # Save to file
    with open("data_records.json", "w") as f:
        json.dump(all_records, f, indent=4)
    print(f"✅ Saved {len(all_records)} records to 'data_records.json'")

if __name__ == "__main__":
    fetch_records_with_numbers()