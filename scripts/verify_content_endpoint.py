import requests
import sys

def verify_endpoint():
    try:
        url = "http://127.0.0.1:5000/content?status=relevant"
        print(f"Checking {url}...")
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"Failed: Status {response.status_code}")
            sys.exit(1)
            
        content = response.text
        # Check if we have items. We expect at least one "badge" or "card" or table row.
        # In content.html, items are likely in a table or list.
        # Let's look for "FOUNDATION_MODELS" since we know that label exists.
        
        if "FOUNDATION_MODELS" in content:
            print("Success: Found 'FOUNDATION_MODELS' in response.")
        elif "No items found" in content: 
             print("Failed: Response says 'No items found' (if that string exists in template).")
             # If template doesn't have "No items found", we might need another check.
             # counting <tr> tags?
             count = content.count("<tr>")
             print(f"Found {count} table rows.")
             if count > 2: # Header + at least one row
                 print("Success: Table seems populated.")
             else:
                 print("Warning: Table seems empty.")
        else:
            # Fallback check
            if "table-hover" in content:
                 count = content.count("<tr>")
                 print(f"Page loaded. Found {count} rows.")
                 if count > 2:
                     print("Success: Table populated.")
                 else:
                     print("Failure: Table empty.")
            else:
                 print("Failure: Could not find table in response.")
                 
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_endpoint()
