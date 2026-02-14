from src.core.database import SessionLocal
from src.core.models import User

def check_users():
    db = SessionLocal()
    users = db.query(User).all()
    print(f"Total Users: {len(users)}")
    for user in users:
        print(f"- {user.phone_number} (Opt-in: {user.opt_in_status})")

if __name__ == "__main__":
    check_users()
