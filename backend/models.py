"""
Database Models

SQLAlchemy ORM models for the Macro Confluence Hub database.

PRD-035: Supports both sync and async sessions for migration.
- Sync: Used by migrations, CLI scripts, and legacy code
- Async: Used by FastAPI routes for non-blocking I/O
"""

import logging
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean, CheckConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database URL setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/confluence.db")

# PRD-035: Railway uses postgres://, SQLAlchemy requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


def get_async_url(url: str) -> str:
    """Convert sync database URL to async-compatible URL (PRD-035)."""
    if "postgresql" in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif "sqlite" in url:
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return url


# Sync engine (for migrations, CLI scripts, backwards compatibility)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# PRD-035: Async engine with connection pooling
# Note: Async engine creation is deferred to avoid import errors when
# aiosqlite/asyncpg are not installed (e.g., local development without async deps)
ASYNC_DATABASE_URL = get_async_url(DATABASE_URL)

async_engine = None
AsyncSessionLocal = None

try:
    if "postgresql" in ASYNC_DATABASE_URL:
        # PostgreSQL: Use connection pooling for production
        async_engine = create_async_engine(
            ASYNC_DATABASE_URL,
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        logger.info("Initialized async PostgreSQL engine with connection pooling")
    else:
        # SQLite: Simpler setup for development
        async_engine = create_async_engine(
            ASYNC_DATABASE_URL,
            echo=False
        )
        logger.info("Initialized async SQLite engine")

    # PRD-035: Async session factory
    AsyncSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
except ModuleNotFoundError as e:
    logger.warning(f"Async database support not available: {e}. Install aiosqlite/asyncpg for async support.")

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


class ServiceHeartbeat(Base):
    """
    Service heartbeat tracking for monitoring (PRD-035).

    Tracks when critical services (like Discord collector on laptop) last checked in.
    Migrated from legacy heartbeat table using raw SQL.
    """
    __tablename__ = "service_heartbeats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(String, nullable=False, unique=True)
    last_heartbeat = Column(DateTime, nullable=False)
    heartbeat_count = Column(Integer, default=0)
    status = Column(String, default="healthy")  # "healthy", "stale", "never_connected"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ServiceHeartbeat(service='{self.service_name}', status='{self.status}')>"


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


class SynthesisFeedback(Base):
    """
    User feedback on research synthesis (PRD-038).

    Supports both simple thumbs up/down and detailed ratings.
    One feedback entry per user per synthesis (upsert pattern).
    """
    __tablename__ = "synthesis_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    synthesis_id = Column(Integer, ForeignKey("syntheses.id", ondelete="CASCADE"), nullable=False)

    # Simple feedback (thumbs up/down)
    is_helpful = Column(Boolean)  # True=thumbs up, False=thumbs down, None=no simple vote

    # Detailed feedback (from modal)
    accuracy_rating = Column(Integer)  # 1-5 scale
    usefulness_rating = Column(Integer)  # 1-5 scale
    comment = Column(Text)

    # Metadata
    user = Column(String, nullable=False)  # Username from JWT
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    synthesis = relationship("Synthesis", backref="feedback_items")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint('accuracy_rating >= 1 AND accuracy_rating <= 5', name='check_synthesis_accuracy_rating'),
        CheckConstraint('usefulness_rating >= 1 AND usefulness_rating <= 5', name='check_synthesis_usefulness_rating'),
        Index('idx_synthesis_feedback_user', 'synthesis_id', 'user'),
    )

    def __repr__(self):
        return f"<SynthesisFeedback(id={self.id}, synthesis_id={self.synthesis_id}, user='{self.user}')>"


class ThemeFeedback(Base):
    """
    User feedback on tracked themes (PRD-038).

    Supports both simple thumbs up/down (relevance) and detailed quality rating.
    One feedback entry per user per theme (upsert pattern).
    """
    __tablename__ = "theme_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    theme_id = Column(Integer, ForeignKey("themes.id", ondelete="CASCADE"), nullable=False)

    # Simple feedback (thumbs up/down for relevance)
    is_relevant = Column(Boolean)  # True=relevant, False=not relevant, None=no vote

    # Detailed feedback (from modal)
    quality_rating = Column(Integer)  # 1-5 scale
    comment = Column(Text)

    # Metadata
    user = Column(String, nullable=False)  # Username from JWT
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    theme = relationship("Theme", backref="feedback_items")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint('quality_rating >= 1 AND quality_rating <= 5', name='check_theme_quality_rating'),
        Index('idx_theme_feedback_user', 'theme_id', 'user'),
    )

    def __repr__(self):
        return f"<ThemeFeedback(id={self.id}, theme_id={self.theme_id}, user='{self.user}')>"


# ============================================================================
# PRD-044: Synthesis Quality Evaluator Model
# ============================================================================

class SynthesisQualityScore(Base):
    """
    AI-evaluated quality scores for synthesis outputs (PRD-044).

    Tracks quality across 7 domain-relevant criteria and provides
    actionable feedback for improving synthesis prompts.
    """
    __tablename__ = "synthesis_quality_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    synthesis_id = Column(Integer, ForeignKey("syntheses.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Overall score (0-100) and letter grade
    quality_score = Column(Integer, nullable=False)
    grade = Column(String(2), nullable=False)  # A+, A, A-, B+, B, B-, C+, C, C-, D, F

    # Individual criterion scores (0-3 scale: 0=fail, 1=poor, 2=acceptable, 3=good)
    # Confluence: Are cross-source alignments identified?
    confluence_detection = Column(Integer, nullable=False)
    # Evidence: Do themes have supporting data points?
    evidence_preservation = Column(Integer, nullable=False)
    # Attribution: Can insights be traced to specific sources?
    source_attribution = Column(Integer, nullable=False)
    # YouTube: Are channels named individually (not generic "YouTube")?
    youtube_channel_granularity = Column(Integer, nullable=False)
    # Nuance: Are conflicting views within sources captured?
    nuance_retention = Column(Integer, nullable=False)
    # Actionability: Are there specific levels, triggers, timeframes?
    actionability = Column(Integer, nullable=False)
    # Continuity: Does it reference theme evolution over time?
    theme_continuity = Column(Integer, nullable=False)

    # Detailed feedback (stored as JSON)
    flags = Column(Text)  # JSON: Array of {criterion, score, detail}
    prompt_suggestions = Column(Text)  # JSON: Array of improvement suggestions

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to Synthesis
    synthesis = relationship("Synthesis", backref="quality_score")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint('quality_score >= 0 AND quality_score <= 100', name='check_quality_score_range'),
        CheckConstraint('confluence_detection >= 0 AND confluence_detection <= 3', name='check_confluence_score'),
        CheckConstraint('evidence_preservation >= 0 AND evidence_preservation <= 3', name='check_evidence_score'),
        CheckConstraint('source_attribution >= 0 AND source_attribution <= 3', name='check_attribution_score'),
        CheckConstraint('youtube_channel_granularity >= 0 AND youtube_channel_granularity <= 3', name='check_youtube_score'),
        CheckConstraint('nuance_retention >= 0 AND nuance_retention <= 3', name='check_nuance_score'),
        CheckConstraint('actionability >= 0 AND actionability <= 3', name='check_actionability_score'),
        CheckConstraint('theme_continuity >= 0 AND theme_continuity <= 3', name='check_continuity_score'),
        CheckConstraint(
            "grade IN ('A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F')",
            name='check_grade_values'
        ),
        Index('idx_quality_synthesis', 'synthesis_id'),
        Index('idx_quality_score', 'quality_score'),
        Index('idx_quality_grade', 'grade'),
    )

    def __repr__(self):
        return f"<SynthesisQualityScore(id={self.id}, synthesis_id={self.synthesis_id}, grade='{self.grade}', score={self.quality_score})>"


class SymbolLevel(Base):
    """
    Price levels per symbol from various sources (PRD-039).

    Stores support, resistance, targets, invalidation levels extracted
    from KT Technical (Elliott Wave) and Discord Options Insight.
    """
    __tablename__ = "symbol_levels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    source = Column(String(20), nullable=False)  # kt_technical, discord

    # Level details
    level_type = Column(String(20), nullable=False)
    # Types: support, resistance, target, invalidation, gamma, volume_shelf, fib_level
    price = Column(Float, nullable=False)
    price_upper = Column(Float)  # For ranges like "313-319"
    significance = Column(String(10))  # critical, important, minor

    # Direction vector - disambiguates how to trade the level
    # "support at 313" (bullish_reversal) vs "breakdown below 313" (bearish_breakdown)
    direction = Column(String(20))
    # Values: bullish_reversal, bearish_reversal, bullish_breakout, bearish_breakdown, neutral

    # Context from source
    wave_context = Column(String(100))  # "wave iv support", "wave 5 target"
    options_context = Column(String(100))  # "peak gamma", "put wall", "volume shelf"
    fib_level = Column(String(10))  # "0.236", "0.382", "0.5", "0.618", "1.236"

    # Context snippet for verification (5-10 words surrounding the extraction)
    context_snippet = Column(String(200))  # e.g., "support likely holding at 313 if bulls defend"

    # Extraction metadata
    confidence = Column(Float, default=0.8)  # 0.0-1.0, flag for review if < 0.7
    extracted_from_content_id = Column(Integer, ForeignKey("raw_content.id"))
    extraction_method = Column(String(20))  # transcript, chart_image, text_post, compass_image

    # Validity tracking
    is_active = Column(Boolean, default=True)
    invalidation_price = Column(Float)  # Price at which this level becomes invalid (extracted from KT)
    invalidated_at = Column(DateTime)  # When manually marked invalid
    invalidation_reason = Column(String(100))

    # Staleness (14-day default)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_confirmed_at = Column(DateTime, default=datetime.utcnow)
    is_stale = Column(Boolean, default=False)
    stale_reason = Column(String(100))

    # Relationships
    raw_content = relationship("RawContent", foreign_keys=[extracted_from_content_id])

    # Constraints and indexes
    __table_args__ = (
        Index('idx_symbol_source', 'symbol', 'source'),
        Index('idx_symbol_active', 'symbol', 'is_active'),
        CheckConstraint(
            "direction IN ('bullish_reversal', 'bearish_reversal', 'bullish_breakout', 'bearish_breakdown', 'neutral')",
            name='check_direction_values'
        ),
    )

    def __repr__(self):
        return f"<SymbolLevel(id={self.id}, symbol='{self.symbol}', type='{self.level_type}', price={self.price})>"


class SymbolState(Base):
    """
    Current consolidated state per symbol (PRD-039).

    Aggregates the latest KT Technical and Discord views for each tracked symbol.
    """
    __tablename__ = "symbol_states"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False, unique=True, index=True)

    # KT Technical state
    kt_wave_degree = Column(String(20))  # minor, intermediate, primary
    kt_wave_position = Column(String(20))  # wave_1, wave_2, wave_3, wave_4, wave_5
    kt_wave_direction = Column(String(10))  # up, down (impulse direction)
    kt_wave_phase = Column(String(15))  # impulse (trending) or correction (choppy)
    kt_bias = Column(String(10))  # bullish, bearish, neutral
    kt_primary_target = Column(Float)
    kt_primary_support = Column(Float)
    kt_invalidation = Column(Float)
    kt_notes = Column(Text)  # AI-extracted key points
    kt_last_updated = Column(DateTime)
    kt_is_stale = Column(Boolean, default=False)
    kt_stale_warning = Column(String(100))
    kt_source_content_id = Column(Integer, ForeignKey("raw_content.id"))

    # Discord Options state
    discord_quadrant = Column(String(20))  # buy_call, buy_put, sell_call, sell_put, neutral
    discord_iv_regime = Column(String(15))  # cheap, neutral, expensive
    discord_strategy_rec = Column(String(100))  # "call spreads", "put calendars", etc.
    discord_key_strikes = Column(Text)  # JSON array of important strikes
    discord_notes = Column(Text)
    discord_last_updated = Column(DateTime)
    discord_is_stale = Column(Boolean, default=False)
    discord_source_content_id = Column(Integer, ForeignKey("raw_content.id"))

    # Confluence scoring
    # NOTE: Confluence requires DIRECTION alignment, not just price proximity
    # "Support at 313" (bullish) + "Buy Call quadrant" (bullish) = HIGH confluence
    # "Support at 313" (bullish) + "Sell Call quadrant" (bearish) = CONFLICT, not confluence
    sources_directionally_aligned = Column(Boolean)  # Both bullish or both bearish
    confluence_score = Column(Float)  # 0.0 to 1.0
    confluence_summary = Column(Text)  # AI-generated alignment analysis
    trade_setup_suggestion = Column(Text)  # AI-generated trade idea when aligned

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    kt_source_content = relationship("RawContent", foreign_keys=[kt_source_content_id])
    discord_source_content = relationship("RawContent", foreign_keys=[discord_source_content_id])

    def __repr__(self):
        return f"<SymbolState(id={self.id}, symbol='{self.symbol}', confluence={self.confluence_score})>"


# ============================================================================
# PRD-045: Collection Monitoring & Alerting Models
# ============================================================================

class TranscriptionStatus(Base):
    """
    Track individual video transcription status (PRD-045).

    Solves the silent failure problem where async transcription tasks
    could fail without any database record of the failure.
    """
    __tablename__ = "transcription_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey("raw_content.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Status tracking
    # Values: pending, processing, completed, failed, skipped
    status = Column(String(20), nullable=False, default="pending")

    error_message = Column(Text)  # If failed, why
    retry_count = Column(Integer, default=0)
    last_attempt_at = Column(DateTime)
    completed_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    content = relationship("RawContent", backref="transcription_status")

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_transcription_status', 'status'),
        Index('idx_transcription_content', 'content_id'),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'skipped')",
            name='check_transcription_status_values'
        ),
    )

    def __repr__(self):
        return f"<TranscriptionStatus(id={self.id}, content_id={self.content_id}, status='{self.status}')>"


class SourceHealth(Base):
    """
    Cached health metrics per source (PRD-045).

    Provides at-a-glance health status for each data source,
    updated periodically or on collection events.
    """
    __tablename__ = "source_health"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String(50), nullable=False, unique=True)

    # Last collection info
    last_collection_at = Column(DateTime)
    last_collection_status = Column(String(20))  # success, partial, failed

    # For video sources (YouTube, Discord videos, 42macro videos)
    last_transcription_at = Column(DateTime)

    # 24-hour metrics
    items_collected_24h = Column(Integer, default=0)
    items_transcribed_24h = Column(Integer, default=0)
    errors_24h = Column(Integer, default=0)

    # Failure tracking
    consecutive_failures = Column(Integer, default=0)

    # Staleness (no new content in 48+ hours)
    is_stale = Column(Boolean, default=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_source_health_name', 'source_name'),
        CheckConstraint(
            "last_collection_status IN ('success', 'partial', 'failed') OR last_collection_status IS NULL",
            name='check_collection_status_values'
        ),
    )

    def __repr__(self):
        return f"<SourceHealth(source='{self.source_name}', stale={self.is_stale}, failures={self.consecutive_failures})>"


class Alert(Base):
    """
    System alerts for collection/transcription issues (PRD-045).

    Stores alerts that are displayed on the dashboard and can be
    acknowledged by users.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Alert classification
    alert_type = Column(String(50), nullable=False)
    # Types: collection_failed, transcription_backlog, source_stale, error_spike
    source = Column(String(50))  # Which source this alert is about (optional)
    severity = Column(String(20), nullable=False)  # critical, high, medium, low
    message = Column(Text, nullable=False)

    # Acknowledgment
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String(100))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # Auto-dismiss after this time

    # Indexes and constraints
    __table_args__ = (
        Index('idx_alert_type', 'alert_type'),
        Index('idx_alert_source', 'source'),
        Index('idx_alert_acknowledged', 'is_acknowledged'),
        Index('idx_alert_severity', 'severity'),
        CheckConstraint(
            "severity IN ('critical', 'high', 'medium', 'low')",
            name='check_alert_severity_values'
        ),
        CheckConstraint(
            "alert_type IN ('collection_failed', 'transcription_backlog', 'source_stale', 'error_spike')",
            name='check_alert_type_values'
        ),
    )

    def __repr__(self):
        return f"<Alert(id={self.id}, type='{self.alert_type}', severity='{self.severity}', ack={self.is_acknowledged})>"


# ============================================================================
# Utility Functions
# ============================================================================

def get_db():
    """Dependency for FastAPI routes to get sync database session (legacy)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """
    Dependency for FastAPI routes to get async database session (PRD-035).

    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()

    Raises:
        RuntimeError: If async database support is not available
    """
    if AsyncSessionLocal is None:
        raise RuntimeError(
            "Async database support not available. "
            "Install aiosqlite (for SQLite) or asyncpg (for PostgreSQL)."
        )
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def drop_all_tables():
    """Drop all tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
