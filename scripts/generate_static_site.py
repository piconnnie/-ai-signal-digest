import requests
import os
import shutil

BASE_URL = "http://127.0.0.1:5000"
OUTPUT_DIR = "docs" # GitHub Pages defaults to /docs

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def save_url(path, filename):
    url = f"{BASE_URL}{path}"
    print(f"Fetching {url}...")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            filepath = os.path.join(OUTPUT_DIR, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"Saved {filepath}")
        else:
            print(f"Failed to fetch {url}: {response.status_code}")
    except Exception as e:
        print(f"Error fetching {url}: {e}")

def generate_static_site():
    # 1. Prepare Output Directory
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    ensure_dir(OUTPUT_DIR)
    
    # 2. Fetch Pages
    # Determine what pages we have.
    # We have index, content (all), content (relevant), content (synthesized), and details.
    
    save_url("/", "index.html")
    save_url("/content", "content.html")
    # For query params, we might need to save them as distinct files if we want them reachable via simple links
    # But standard GitHub Pages processing might be tricky with query params.
    # Let's save them as distinct HTML files and maybe update links in a post-process step?
    # Or just save the views we care about.
    
    save_url("/content?status=relevant", "relevant.html")
    save_url("/content?status=synthesized", "synthesized.html")
    
    # We also need detail pages for all items.
    # Let's fetch the list of items from the DB or just parse the Content page?
    # Better to ask the DB for IDs.
    
    from src.core.database import SessionLocal
    from src.core.models import Content
    
    db = SessionLocal()
    items = db.query(Content.id).all()
    
    ensure_dir(os.path.join(OUTPUT_DIR, "item"))
    
    for item in items:
        item_id = item[0]
        # We need to save as item/{id}.html because that matches /item/{id} content if configured right,
        # or item/{id}/index.html for clean URLs.
        # Let's use item_{id}.html for simplicity and flat structure?
        # But links in app are /item/1. 
        # On GH Pages, /item/1 would look for item/1/index.html or item/1.html.
        
        # Let's save as item/{id}.html
        save_url(f"/item/{item_id}", f"item/{item_id}.html")

    print("\nStatic site generation complete.")
    print(f"Files saved to '{OUTPUT_DIR}/'. You can push this folder to GitHub.")
    print("NOTE: Search/Filter parameters in URLs won't work dynamically. Links might need adjustment.")

if __name__ == "__main__":
    generate_static_site()
