"""
Database connection and session management for Sovereign AI.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from typing import Generator

from .models import Base

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/sovereign_ai.db")

# Create engine with appropriate configuration
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )
else:
    engine = create_engine(DATABASE_URL, echo=os.getenv("DEBUG", "false").lower() == "true")

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize the database with tables and default data."""
    create_tables()
    
    # Create data directory if it doesn't exist
    data_dir = os.path.dirname(DATABASE_URL.replace("sqlite:///", ""))
    if data_dir and not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    
    print("Database initialized successfully")

