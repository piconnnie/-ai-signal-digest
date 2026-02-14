from src.core.database import SessionLocal
from src.core.models import Content

def check_counts():
    db = SessionLocal()
    
    total = db.query(Content).count()
    relevant = db.query(Content).filter(Content.relevance_label != 'IRRELEVANT', Content.relevance_label.isnot(None)).count()
    synthesized = db.query(Content).filter(Content.summary_headline.isnot(None)).count()
    pending = db.query(Content).filter(Content.relevance_label == None).count()
    
    print(f"Total: {total}")
    print(f"Relevant: {relevant}")
    print(f"Synthesized: {synthesized}")
    print(f"Pending: {pending}")

if __name__ == "__main__":
    check_counts()
