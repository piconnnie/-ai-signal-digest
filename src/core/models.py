from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, ConfigDict
from .database import Base

# --- SQLAlchemy Models ---

class Content(Base):
    __tablename__ = "content"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, index=True) # arxiv, techcrunch, etc.
    type = Column(String, index=True)   # research, news
    title = Column(String, index=True)
    url = Column(String, unique=True, index=True)
    published_at = Column(DateTime, index=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    
    # Raw Content
    abstract_or_body = Column(Text)
    authors = Column(JSON, default=list) # List of strings

    # Enrichment
    topics = Column(JSON, default=list)
    embedding_vector = Column(JSON, nullable=True) # Stored as list of floats
    
    # Relevance
    relevance_label = Column(String, nullable=True)
    relevance_confidence = Column(Float, nullable=True)
    relevance_reason = Column(Text, nullable=True)
    
    # Prioritization
    priority_score = Column(Float, default=0.0)
    cluster_id = Column(String, nullable=True)

    # Synthesis
    summary_headline = Column(String, nullable=True)
    summary_tldr = Column(Text, nullable=True)
    summary_highlights = Column(JSON, default=list)
    summary_why_matters = Column(Text, nullable=True)
    
    # Validation
    validation_status = Column(String, default="PENDING") # PENDING, PASS, FAIL
    
    # Delivery Status (Simple tracking for now)
    delivery_status = Column(String, default="PENDING")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True)
    opt_in_status = Column(Boolean, default=True)
    topic_preferences = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

# --- Pydantic Models for Data Transfer ---

class ContentBase(BaseModel):
    source: str
    type: str
    title: str
    url: str
    published_at: datetime
    abstract_or_body: str
    authors: List[str] = []

class ContentCreate(ContentBase):
    pass

class ContentRead(ContentBase):
    id: int
    fetched_at: datetime
    topics: List[str] = []
    relevance_label: Optional[str] = None
    summary_headline: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class EnrichedContent(ContentRead):
    embedding_vector: Optional[List[float]] = None

class InsightSummary(BaseModel):
    headline: str = Field(..., max_length=120)
    tldr: str
    highlights: List[str]
    why_it_matters: str
    source_url: str

class UserCreate(BaseModel):
    phone_number: str
    topic_preferences: List[str] = []
