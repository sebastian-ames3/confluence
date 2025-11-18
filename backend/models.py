"""
Database Models

SQLAlchemy ORM models for the Macro Confluence Hub database.
These models will be fully implemented in Phase 1 (PRD-002).
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/confluence.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# TODO: Implement full models in Phase 1 (PRD-002):
# - Source model
# - RawContent model
# - AnalyzedContent model
# - ConfluenceScore model
# - Theme model
# - ThemeTracking model
# - UserAction model


class SchemaVersion(Base):
    """Track database schema versions."""
    __tablename__ = "schema_version"

    version = Column(Integer, primary_key=True)
    applied_at = Column(DateTime, default=datetime.utcnow)
    description = Column(Text)


def get_db():
    """Dependency for FastAPI routes to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
