import sys
import os

# Add project root to sys.path to allow imports from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_frozen import Freezer
from src.ui.app import app, get_db_session
from src.core.models import Content

# Configure Freezer
app.config['FREEZER_DESTINATION'] = '../../docs' # GitHub Pages default
app.config['FREEZER_RELATIVE_URLS'] = True       # Essential for GH Pages subdirectory hosting

# Clean output directory
import shutil
if os.path.exists(os.path.join(os.path.dirname(__file__), '../../docs')):
    shutil.rmtree(os.path.join(os.path.dirname(__file__), '../../docs'))

freezer = Freezer(app)

@freezer.register_generator
def content_detail():
    with get_db_session() as db:
        items = db.query(Content.id).all()
        for item in items:
            yield {'item_id': item[0]}

if __name__ == '__main__':
    print("Clean docs/...")
    if os.path.exists(os.path.join(os.path.dirname(__file__), '../../docs')):
        shutil.rmtree(os.path.join(os.path.dirname(__file__), '../../docs'))

    print("Freezing application to /docs folder...")
    
    # Debug: Print URLs
    try:
        for url in freezer.all_urls():
            print(f"Generating: {url}")
    except Exception as e:
        print(f"Error listing URLs: {e}")

    freezer.freeze()
    print("Done! The 'docs' folder contains the static site.")
    print("To publish: Push the 'docs' folder to your GitHub repository.")
