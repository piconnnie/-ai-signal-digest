from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import desc
from src.core.database import SessionLocal, init_db
from src.core.models import Content
from src.core.config import Config
from src.main import run_pipeline
import threading

app = Flask(__name__)

# Ensure DB is ready
init_db()

def get_db_session():
    return SessionLocal()

@app.route('/')
def index():
    """Dashboard view."""
    with get_db_session() as db:
        total_content = db.query(Content).count()
        pending_relevance = db.query(Content).filter(Content.relevance_label == None).count()
        relevant_items = db.query(Content).filter(Content.relevance_label.notin_(['IRRELEVANT', None])).count()
        synthesized = db.query(Content).filter(Content.summary_headline.isnot(None)).count()
        delivered = db.query(Content).filter(Content.delivery_status == 'SENT').count()
        
        # Recent activity
        recent_items = db.query(Content).order_by(Content.fetched_at.desc()).limit(5).all()
        
    stats = {
        "total": total_content,
        "pending_rel": pending_relevance,
        "relevant": relevant_items,
        "synthesized": synthesized,
        "delivered": delivered
    }
    return render_template('index.html', stats=stats, recent=recent_items)

@app.route('/content')
def content_list():
    """List all content with filters."""
    filter_status = request.args.get('status', 'all')
    
    with get_db_session() as db:
        query = db.query(Content).order_by(Content.fetched_at.desc())
        
        if filter_status == 'relevant':
             query = query.filter(Content.relevance_label.notin_(['IRRELEVANT', None]))
        elif filter_status == 'synthesized':
             query = query.filter(Content.summary_headline.isnot(None))
        elif filter_status == 'pending':
             query = query.filter(Content.relevance_label == None)
             
        items = query.limit(50).all()
        
    return render_template('content.html', items=items, filter=filter_status)

@app.route('/item/<int:item_id>')
def content_detail(item_id):
    with get_db_session() as db:
        item = db.query(Content).get(item_id)
        if not item:
            return "Item not found", 404
        return render_template('detail.html', item=item)

@app.route('/run_pipeline', methods=['POST'])
def trigger_pipeline():
    """Manually trigger the pipeline in a background thread."""
    def run_job():
        print("Manual pipeline run started...")
        run_pipeline()
        print("Manual pipeline run finished.")
        
    thread = threading.Thread(target=run_job)
    thread.start()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False) # Disable reloader for thread safety in simple test
