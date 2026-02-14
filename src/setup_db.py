from src.core.database import init_db
from src.core.models import Base 
# Must import models so Base knows about them before create_all

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized.")
