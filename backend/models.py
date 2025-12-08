"""
Database Models

SQLAlchemy ORM models for the Macro Confluence Hub database.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean, CheckConstraint, Index
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


# ============================================================================
# ORM Models
# ============================================================================

class Source(Base):
    """Data source configuration (42macro, Discord, Twitter, etc.)"""
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    type = Column(String, nullable=False)  # "web", "discord", "twitter", "youtube", "rss"
    config = Column(Text)  # JSON configuration
    active = Column(Boolean, default=True)
    last_collected_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    raw_content_items = relationship("RawContent", back_populates="source", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Source(id={self.id}, name='{self.name}', type='{self.type}')>"


class RawContent(Base):
    """Collected content before AI analysis"""
    __tablename__ = "raw_content"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    content_type = Column(String, nullable=False)  # "text", "pdf", "video", "image"
    content_text = Column(Text)
    file_path = Column(String)
    url = Column(String, index=True)  # Indexed for duplicate detection
    json_metadata = Column(Text)  # JSON metadata
    collected_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)

    # Relationships
    source = relationship("Source", back_populates="raw_content_items")
    analyzed_items = relationship("AnalyzedContent", back_populates="raw_content", cascade="all, delete-orphan")

    # Indexes for efficient duplicate detection (PRD-019)
    __table_args__ = (
        Index('idx_source_url', 'source_id', 'url'),
        Index('idx_source_content_type', 'source_id', 'content_type'),
    )

    def __repr__(self):
        return f"<RawContent(id={self.id}, type='{self.content_type}', source_id={self.source_id})>"


class AnalyzedContent(Base):
    """AI agent analysis results"""
    __tablename__ = "analyzed_content"

    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_content_id = Column(Integer, ForeignKey("raw_content.id", ondelete="CASCADE"), nullable=False)
    agent_type = Column(String, nullable=False)  # "transcript", "pdf", "image", "classifier"
    analysis_result = Column(Text, nullable=False)  # JSON full output
    key_themes = Column(Text)  # Comma-separated
    tickers_mentioned = Column(Text)  # Comma-separated
    sentiment = Column(String)  # "bullish", "bearish", "neutral"
    conviction = Column(Integer)  # 0-10
    time_horizon = Column(String)  # "1d", "1w", "1m", "3m", "6m+"
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    raw_content = relationship("RawContent", back_populates="analyzed_items")
    confluence_scores = relationship("ConfluenceScore", back_populates="analyzed_content", cascade="all, delete-orphan")
    theme_evidence_items = relationship("ThemeEvidence", back_populates="analyzed_content", cascade="all, delete-orphan")
    bayesian_updates = relationship("BayesianUpdate", back_populates="analyzed_content")

    def __repr__(self):
        return f"<AnalyzedContent(id={self.id}, agent='{self.agent_type}', raw_id={self.raw_content_id})>"


class ConfluenceScore(Base):
    """Pillar-by-pillar confluence scores"""
    __tablename__ = "confluence_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analyzed_content_id = Column(Integer, ForeignKey("analyzed_content.id", ondelete="CASCADE"), nullable=False)

    # Core 5 pillars (0-2 each)
    macro_score = Column(Integer, nullable=False)
    fundamentals_score = Column(Integer, nullable=False)
    valuation_score = Column(Integer, nullable=False)
    positioning_score = Column(Integer, nullable=False)
    policy_score = Column(Integer, nullable=False)

    # Hybrid 2 pillars (0-2 each)
    price_action_score = Column(Integer, nullable=False)
    options_vol_score = Column(Integer, nullable=False)

    # Totals
    core_total = Column(Integer, nullable=False)
    total_score = Column(Integer, nullable=False)
    meets_threshold = Column(Boolean, nullable=False)

    # Reasoning
    reasoning = Column(Text, nullable=False)
    falsification_criteria = Column(Text)  # JSON

    scored_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    analyzed_content = relationship("AnalyzedContent", back_populates="confluence_scores")

    # Constraints
    __table_args__ = (
        CheckConstraint('macro_score >= 0 AND macro_score <= 2', name='check_macro_score'),
        CheckConstraint('fundamentals_score >= 0 AND fundamentals_score <= 2', name='check_fundamentals_score'),
        CheckConstraint('valuation_score >= 0 AND valuation_score <= 2', name='check_valuation_score'),
        CheckConstraint('positioning_score >= 0 AND positioning_score <= 2', name='check_positioning_score'),
        CheckConstraint('policy_score >= 0 AND policy_score <= 2', name='check_policy_score'),
        CheckConstraint('price_action_score >= 0 AND price_action_score <= 2', name='check_price_action_score'),
        CheckConstraint('options_vol_score >= 0 AND options_vol_score <= 2', name='check_options_vol_score'),
    )

    def __repr__(self):
        return f"<ConfluenceScore(id={self.id}, total={self.total_score}, meets_threshold={self.meets_threshold})>"


class Theme(Base):
    """Investment themes being tracked (PRD-024)"""
    __tablename__ = "themes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)

    # PRD-024: Theme aliases (JSON array of alternative expressions)
    aliases = Column(Text)  # JSON array

    # PRD-024: Theme evolution tracking
    evolved_from_theme_id = Column(Integer, ForeignKey("themes.id"))

    # PRD-024: Per-source evidence (JSON with source-specific evidence)
    source_evidence = Column(Text)  # JSON: {"42macro": [...], "discord": [...]}

    # PRD-024: Related catalysts (JSON array)
    catalysts = Column(Text)  # JSON array

    # PRD-024: First source to mention theme
    first_source = Column(String)

    # Theme lifecycle (PRD-024: emerging -> active -> evolved -> dormant)
    first_mentioned_at = Column(DateTime)
    status = Column(String, default='emerging')  # "emerging", "active", "evolved", "dormant"
    last_updated_at = Column(DateTime)

    # Legacy fields (kept for backwards compatibility, not actively used in PRD-024)
    current_conviction = Column(Float, default=0.5)  # Not used in PRD-024 approach
    confidence_interval_low = Column(Float)
    confidence_interval_high = Column(Float)
    prior_probability = Column(Float)
    evidence_count = Column(Integer, default=0)

    json_metadata = Column(Text)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    evidence_items = relationship("ThemeEvidence", back_populates="theme", cascade="all, delete-orphan")
    bayesian_updates = relationship("BayesianUpdate", back_populates="theme", cascade="all, delete-orphan")
    evolved_from = relationship("Theme", remote_side=[id], backref="evolved_into")

    # Constraints - updated for PRD-024 lifecycle
    __table_args__ = (
        CheckConstraint("status IN ('emerging', 'active', 'evolved', 'dormant')", name='check_status_values'),
    )

    def __repr__(self):
        return f"<Theme(id={self.id}, name='{self.name}', status='{self.status}')>"


class ThemeEvidence(Base):
    """Links analyzed content to themes (many-to-many)"""
    __tablename__ = "theme_evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    theme_id = Column(Integer, ForeignKey("themes.id", ondelete="CASCADE"), nullable=False)
    analyzed_content_id = Column(Integer, ForeignKey("analyzed_content.id", ondelete="CASCADE"), nullable=False)
    supports_theme = Column(Boolean, default=True)
    evidence_strength = Column(Float, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    theme = relationship("Theme", back_populates="evidence_items")
    analyzed_content = relationship("AnalyzedContent", back_populates="theme_evidence_items")

    # Constraints
    __table_args__ = (
        CheckConstraint('evidence_strength >= 0.0 AND evidence_strength <= 1.0', name='check_evidence_strength'),
    )

    def __repr__(self):
        return f"<ThemeEvidence(id={self.id}, theme_id={self.theme_id}, strength={self.evidence_strength:.2f})>"


class BayesianUpdate(Base):
    """Tracks conviction changes over time"""
    __tablename__ = "bayesian_updates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    theme_id = Column(Integer, ForeignKey("themes.id", ondelete="CASCADE"), nullable=False)
    prior_conviction = Column(Float, nullable=False)
    posterior_conviction = Column(Float, nullable=False)
    evidence_analyzed_content_id = Column(Integer, ForeignKey("analyzed_content.id", ondelete="SET NULL"))
    update_reason = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    theme = relationship("Theme", back_populates="bayesian_updates")
    analyzed_content = relationship("AnalyzedContent", back_populates="bayesian_updates")

    # Constraints
    __table_args__ = (
        CheckConstraint('prior_conviction >= 0.0 AND prior_conviction <= 1.0', name='check_prior_conviction'),
        CheckConstraint('posterior_conviction >= 0.0 AND posterior_conviction <= 1.0', name='check_posterior_conviction'),
    )

    def __repr__(self):
        return f"<BayesianUpdate(id={self.id}, theme_id={self.theme_id}, {self.prior_conviction:.2f}->{self.posterior_conviction:.2f})>"


class Synthesis(Base):
    """AI-generated research synthesis summaries"""
    __tablename__ = "syntheses"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Schema version for backwards compatibility (PRD-020)
    schema_version = Column(String(10), default="1.0")  # "1.0" or "2.0"

    # Synthesis content (v1 fields - kept for backwards compatibility)
    synthesis = Column(Text, nullable=False)  # v1: full text, v2: synthesis_summary
    key_themes = Column(Text)  # JSON array
    high_conviction_ideas = Column(Text)  # JSON array
    contradictions = Column(Text)  # JSON array
    market_regime = Column(String)  # "risk-on", "risk-off", "transitioning", "unclear"
    catalysts = Column(Text)  # JSON array

    # V2: Full JSON response (PRD-020)
    synthesis_json = Column(Text)  # Complete v2 JSON response with tactical/strategic ideas

    # Metadata
    time_window = Column(String, nullable=False)  # "24h", "7d", "30d"
    content_count = Column(Integer, default=0)
    sources_included = Column(Text)  # JSON array

    # Optional focus
    focus_topic = Column(String)

    # Cost tracking
    token_usage = Column(Integer)

    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Synthesis(id={self.id}, time_window='{self.time_window}', generated_at={self.generated_at})>"


class CollectionRun(Base):
    """Tracks collection runs for status display"""
    __tablename__ = "collection_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Run metadata
    run_type = Column(String, nullable=False)  # "scheduled_6am", "scheduled_6pm", "manual"
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)

    # Results per source (JSON object)
    source_results = Column(Text)

    # Totals
    total_items_collected = Column(Integer, default=0)
    successful_sources = Column(Integer, default=0)
    failed_sources = Column(Integer, default=0)

    # Error tracking
    errors = Column(Text)  # JSON array

    # Status
    status = Column(String, default='running')  # "running", "completed", "failed"

    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('running', 'completed', 'failed')", name='check_run_status'),
    )

    def __repr__(self):
        return f"<CollectionRun(id={self.id}, type='{self.run_type}', status='{self.status}')>"


# ============================================================================
# Utility Functions
# ============================================================================

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


def drop_all_tables():
    """Drop all tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
