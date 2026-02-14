from src.core.database import SessionLocal
from src.core.models import Content
from sqlalchemy import func

def check_db():
    db = SessionLocal()
    results = db.query(Content.source, func.count(Content.id)).group_by(Content.source).all()
    print("Content Count by Source:")
    for source, count in results:
        print(f"- {source}: {count}")
    
    # Check for clusters
    clusters = db.query(Content.cluster_id, func.count(Content.id)).filter(Content.cluster_id.isnot(None)).group_by(Content.cluster_id).all()
    print(f"\nTotal Clusters: {len(clusters)}")
    if clusters:
        print(f"Sample Cluster: {clusters[0]}")

    # Check validation status
    validation_stats = db.query(Content.validation_status, func.count(Content.id)).group_by(Content.validation_status).all()
    print("\nValidation Status:")
    for status, count in validation_stats:
        print(f"- {status}: {count}")

if __name__ == "__main__":
    check_db()
