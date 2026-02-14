---
name: database-sqlite
description: Patterns for using SQLite with SQLAlchemy and Pydantic.
---

# Database Implementation (SQLite + SQLAlchemy)

## Core Stack
- **SQLite**: Lightweight, file-based database.
- **SQLAlchemy (Core + ORM)**: For database interaction.
- **Pydantic**: For data validation and serialization.

## Configuration
Use a singleton pattern for the database connection.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./data/signal_digest.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## Models (SQLAlchemy + Pydantic)
Separate DB models from Pydantic schemas.

**DB Model:**
```python
from sqlalchemy import Column, Integer, String, Text
from .database import Base

class Content(Base):
    __tablename__ = "content"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    body = Column(Text)
    url = Column(String, unique=True, index=True)
```

**Pydantic Schema:**
```python
from pydantic import BaseModel

class ContentBase(BaseModel):
    title: str
    body: str
    url: str

class ContentCreate(ContentBase):
    pass

class Content(ContentBase):
    id: int
    class Config:
        from_attributes = True
```

## Vector Storage
For simple vector search, store embeddings as BLOBs or use `sqlite-vss` extension if available.
Alternatively, use a separate lightweight vector store like `chromadb` (if permitted) or simple cosine similarity in updates.
