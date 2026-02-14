from src.core.database import SessionLocal
from src.core.models import Content
from sqlalchemy import func

def check_relevance():
    db = SessionLocal()
    results = db.query(Content.relevance_label, func.count(Content.id)).group_by(Content.relevance_label).all()
    print("Relevance Labels Breakdown:")
    for label, count in results:
        print(f"- {label}: {count}")

if __name__ == "__main__":
    check_relevance()
