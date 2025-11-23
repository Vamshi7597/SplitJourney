"""
Database configuration and initialization.
Handles SQLite connection and session creation.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Database file path
DB_FILE = "splitjourney_v2.db"
# Database configuration
# Check for DATABASE_URL environment variable (for production/cloud)
# If not set, fallback to local SQLite file
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_FILE}")

# Configure connection args
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create engine
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def init_db():
    """
    Initialize the database by creating all tables.
    Should be called on app startup.
    """
    # Import models here to ensure they are registered with Base
    from core import models
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at {DB_FILE}")

def get_db():
    """
    Dependency to get a database session.
    Yields a session and closes it after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
