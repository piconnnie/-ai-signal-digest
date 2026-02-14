from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from sqlalchemy import desc
from src.core.database import SessionLocal, init_db
from src.core.models import Content, User
from src.core.config import Config
from src.main import run_pipeline
import threading
import os

app = Flask(__name__)
app.secret_key = os.urandom(24) # Valid for MVP session handling

# Ensure DB is ready
init_db()

def get_db_session():
    return SessionLocal()

def get_lifecycle_status(item):
    """
    Determines the simplified status of an item.
    """
    if item.delivery_status == 'SENT':
        return 'Delivered', 'success'
    if item.validation_status == 'FAIL':
        return 'Rejected', 'danger'
    if item.validation_status == 'PASS':
        return 'Ready', 'info'
    if item.summary_headline:
        return 'Synthesized', 'primary'
    if item.relevance_label == 'IRRELEVANT':
        return 'Irrelevant', 'secondary'
    if item.relevance_label:
        return 'Relevant', 'info' # But not yet synthesized
    return 'Pending', 'warning'

app.add_template_global(get_lifecycle_status, name='get_lifecycle_status')

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

@app.route('/content/')
def content_list():
    """List all content with filters."""
    filter_status = request.args.get('status', 'all')
    return content_list_filtered(filter_status)

@app.route('/relevant/')
def relevant_content():
    return content_list_filtered('relevant')

@app.route('/synthesized/')
def synthesized_content():
    return content_list_filtered('synthesized')

def content_list_filtered(filter_status):
    """Helper for filtered views."""
    with get_db_session() as db:
        query = db.query(Content).order_by(Content.fetched_at.desc())
        
        if filter_status == 'relevant':
             # Explicitly exclude IRRELEVANT and NULL
             query = query.filter(Content.relevance_label != 'IRRELEVANT', Content.relevance_label.isnot(None))
        elif filter_status == 'synthesized':
             query = query.filter(Content.summary_headline.isnot(None))
        elif filter_status == 'pending':
             query = query.filter(Content.relevance_label == None)
             
        items = query.limit(50).all()
        
    return render_template('content.html', items=items, filter=filter_status)

@app.route('/item/<int:item_id>/')
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

@app.route('/subscribe', methods=['POST'])
def subscribe_user():
    phone = request.form.get('phone')
    if not phone:
        return "Phone number required", 400
    
    # Basic normalization (MVP)
    phone = phone.strip().replace(" ", "").replace("-", "")
    
    with get_db_session() as db:
        existing = db.query(User).filter(User.phone_number == phone).first()
        if not existing:
            new_user = User(phone_number=phone, opt_in_status=True)
            db.add(new_user)
            db.commit()
            print(f"New subscriber: {phone}")
            flash("Subscribed successfully! You will receive daily digests at 9 AM.", "success")
        else:
             print(f"Subscriber already exists: {phone}")
             if not existing.opt_in_status:
                 existing.opt_in_status = True
                 db.commit()
                 flash("Welcome back! You have re-subscribed.", "success")
             else:
                 flash("You are already subscribed.", "info")

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False) # Disable reloader for thread safety in simple test
