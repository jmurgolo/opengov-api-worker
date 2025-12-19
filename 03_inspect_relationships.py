import requests
import json
import urllib3
from config import API_KEY, BASE_URL

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# The ID that failed
TEST_ID = "682930"

def inspect_record_relationships():
    print(f"🕵️ INSPECTING RECORD: {TEST_ID}")
    
    headers = {"Authorization": f"Token {API_KEY}", "Accept": "application/json"}
    
    # 1. Fetch the single record directly
    url = f"{BASE_URL}/records/{TEST_ID}"
    
    try:
        resp = requests.get(url, headers=headers, verify=False)
        
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json().get('data', {})
            
            # A. Check Attributes (Is address just a text field?)
            print("\n--- ATTRIBUTES (Is the address here?) ---")
            attrs = data.get('attributes', {})
            for k, v in attrs.items():
                # Print only likely address fields
                if "address" in k.lower() or "location" in k.lower() or "street" in k.lower():
                    print(f"   • {k}: {v}")

            # B. Check Relationships (Where is the data linked?)
            print("\n--- RELATIONSHIPS (The correct links) ---")
            rels = data.get('relationships', {})
            if rels:
                for key, val in rels.items():
                    # The 'related' link tells us the exact URL to use
                    link = val.get('links', {}).get('related')
                    print(f"   • {key}: {link}")
            else:
                print("   (No relationships found)")

        else:
            print(f"❌ Failed to fetch record: {resp.text}")

    except Exception as e:
        print(f"Crash: {e}")

if __name__ == "__main__":
    inspect_record_relationships()