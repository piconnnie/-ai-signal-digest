from src.core.database import SessionLocal
from src.core.models import Content
from datetime import datetime

def insert_test_data():
    db = SessionLocal()
    
    # 1. Pending Item
    pending = Content(
        source="manual_test",
        type="test_data",
        title="Test Pending Item",
        url="http://test.com/pending",
        published_at=datetime.utcnow(),
        abstract_or_body="This is a test item that has not been processed.",
        delivery_status="PENDING",
        validation_status="PENDING"
    )
    
    # 2. Irrelevant Item
    irrelevant = Content(
        source="manual_test",
        type="test_data",
        title="Test Irrelevant Item",
        url="http://test.com/irrelevant",
        published_at=datetime.utcnow(),
        abstract_or_body="This item is about cooking, not AI.",
        relevance_label="IRRELEVANT",
        relevance_reason="Not related to AI.",
        delivery_status="PENDING",
        validation_status="PENDING"
    )
    
    try:
        db.add(pending)
        db.add(irrelevant)
        db.commit()
        print("Inserted 2 test items.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    insert_test_data()
