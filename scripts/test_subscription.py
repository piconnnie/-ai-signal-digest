import requests
import sys

def test_subscribe():
    url = "http://127.0.0.1:5000/subscribe"
    payload = {"phone": "+1234567890"}
    
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Subscription Successful (200 OK)")
            # The app redirects to index, so 200 is good if folllowing redirects, 
            # or 302 if not. requests follows redirects by default.
        else:
            print(f"Subscription Failed: {response.status_code}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_subscribe()
