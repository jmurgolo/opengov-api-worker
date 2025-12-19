import requests
import json
import urllib3
import time
from config import API_KEY, BASE_URL

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_basic_records():
    print("🚀 STEP 1: Fetching Basic Records List...")
    
    headers = {"Authorization": f"Token {API_KEY}", "Accept": "application/json"}
    s = requests.Session()
    s.headers.update(headers)

    all_records = []
    page_num = 1
    page_size = 20 # Can increase this to 50 or 100 for speed
    keep_fetching = True

    while keep_fetching:
        print(f"   Fetching Page {page_num}...", end=" ")
        
        # URL with manual params to avoid encoding issues
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

            # We only keep the ID and Attributes (Strip out links/relationships to save space)
            for item in batch:
                clean_item = {
                    "id": item.get("id"),
                    "attributes": item.get("attributes", {})
                }
                all_records.append(clean_item)

            print(f"Got {len(batch)}. Total: {len(all_records)}")
            
            page_num += 1
            # REMOVE THIS LIMIT TO GET EVERYTHING
            if page_num > 2: keep_fetching = False 

        except Exception as e:
            print(f"\n❌ CRASH: {e}")
            break

    # Save to file
    with open("data_records.json", "w") as f:
        json.dump(all_records, f, indent=4)
    print(f"✅ Saved {len(all_records)} records to 'data_records.json'")

if __name__ == "__main__":
    fetch_basic_records()