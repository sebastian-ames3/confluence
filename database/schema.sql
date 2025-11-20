-- ============================================================================
-- Macro Confluence Hub - Database Schema
-- ============================================================================
-- Version: 1.1
-- Date: 2025-11-20
-- Description: Complete SQLite schema for storing collected content,
--              AI analysis, confluence scores, and theme tracking
-- Changelog v1.1: Added extracted_images table for Chart Intelligence System
-- ============================================================================

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- ============================================================================
-- TABLE: sources
-- Purpose: Configuration for each data source
-- ============================================================================
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,              -- "42macro", "discord_options_insight", etc.
    type TEXT NOT NULL,                     -- "web", "discord", "twitter", "youtube", "rss"
    config TEXT,                            -- JSON: Source-specific configuration
    active BOOLEAN DEFAULT 1,               -- Is this source currently being collected?
    last_collected_at TIMESTAMP,            -- Last successful collection timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABLE: raw_content
-- Purpose: Stores everything collected before AI analysis
-- ============================================================================
CREATE TABLE IF NOT EXISTS raw_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    content_type TEXT NOT NULL,             -- "text", "pdf", "video", "image"
    content_text TEXT,                      -- For text content
    file_path TEXT,                         -- For files (PDFs, videos, images)
    url TEXT,                               -- Original URL if applicable
    json_metadata TEXT,                     -- JSON: Author, timestamp, channel, etc.
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT 0,            -- Has this been analyzed yet?
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
);

-- Indexes for raw_content
CREATE INDEX IF NOT EXISTS idx_raw_content_source ON raw_content(source_id);
CREATE INDEX IF NOT EXISTS idx_raw_content_processed ON raw_content(processed);
CREATE INDEX IF NOT EXISTS idx_raw_content_collected_at ON raw_content(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_raw_content_type ON raw_content(content_type);

-- ============================================================================
-- TABLE: analyzed_content
-- Purpose: Stores AI agent analysis results
-- ============================================================================
CREATE TABLE IF NOT EXISTS analyzed_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_content_id INTEGER NOT NULL,
    agent_type TEXT NOT NULL,               -- "transcript", "pdf", "image", "classifier"
    analysis_result TEXT NOT NULL,          -- JSON: Full structured output from agent
    key_themes TEXT,                        -- Comma-separated themes for quick search
    tickers_mentioned TEXT,                 -- Comma-separated tickers
    sentiment TEXT,                         -- "bullish", "bearish", "neutral"
    conviction INTEGER,                     -- 0-10
    time_horizon TEXT,                      -- "1d", "1w", "1m", "3m", "6m+"
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (raw_content_id) REFERENCES raw_content(id) ON DELETE CASCADE
);

-- Indexes for analyzed_content
CREATE INDEX IF NOT EXISTS idx_analyzed_content_raw ON analyzed_content(raw_content_id);
CREATE INDEX IF NOT EXISTS idx_analyzed_content_themes ON analyzed_content(key_themes);
CREATE INDEX IF NOT EXISTS idx_analyzed_content_tickers ON analyzed_content(tickers_mentioned);
CREATE INDEX IF NOT EXISTS idx_analyzed_content_sentiment ON analyzed_content(sentiment);
CREATE INDEX IF NOT EXISTS idx_analyzed_content_analyzed_at ON analyzed_content(analyzed_at DESC);

-- ============================================================================
-- TABLE: extracted_images
-- Purpose: Stores images extracted from PDFs for visual analysis
-- ============================================================================
CREATE TABLE IF NOT EXISTS extracted_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_content_id INTEGER NOT NULL,        -- Which PDF/content this image came from
    image_path TEXT NOT NULL,               -- File path to extracted image
    page_number INTEGER,                    -- Page number in source PDF (null for web images)
    extraction_method TEXT,                 -- "pymupdf", "web_download", etc.
    content_type TEXT,                      -- "single_chart", "multi_panel", "table", "text_only", "unknown"
    analyzed BOOLEAN DEFAULT 0,             -- Has Image Intelligence Agent analyzed this?
    analyzed_content_id INTEGER,            -- Link to analysis result if analyzed
    json_metadata TEXT,                     -- JSON: Image size, format, detected elements, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (raw_content_id) REFERENCES raw_content(id) ON DELETE CASCADE,
    FOREIGN KEY (analyzed_content_id) REFERENCES analyzed_content(id) ON DELETE SET NULL
);

-- Indexes for extracted_images
CREATE INDEX IF NOT EXISTS idx_extracted_images_raw_content ON extracted_images(raw_content_id);
CREATE INDEX IF NOT EXISTS idx_extracted_images_analyzed ON extracted_images(analyzed);
CREATE INDEX IF NOT EXISTS idx_extracted_images_content_type ON extracted_images(content_type);
CREATE INDEX IF NOT EXISTS idx_extracted_images_created_at ON extracted_images(created_at DESC);

-- ============================================================================
-- TABLE: confluence_scores
-- Purpose: Stores pillar-by-pillar scores for analyzed content
-- ============================================================================
CREATE TABLE IF NOT EXISTS confluence_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analyzed_content_id INTEGER NOT NULL,

    -- Core 5 pillars (0-2 each)
    macro_score INTEGER NOT NULL CHECK(macro_score >= 0 AND macro_score <= 2),
    fundamentals_score INTEGER NOT NULL CHECK(fundamentals_score >= 0 AND fundamentals_score <= 2),
    valuation_score INTEGER NOT NULL CHECK(valuation_score >= 0 AND valuation_score <= 2),
    positioning_score INTEGER NOT NULL CHECK(positioning_score >= 0 AND positioning_score <= 2),
    policy_score INTEGER NOT NULL CHECK(policy_score >= 0 AND policy_score <= 2),

    -- Hybrid 2 pillars (0-2 each)
    price_action_score INTEGER NOT NULL CHECK(price_action_score >= 0 AND price_action_score <= 2),
    options_vol_score INTEGER NOT NULL CHECK(options_vol_score >= 0 AND options_vol_score <= 2),

    -- Totals
    core_total INTEGER NOT NULL,            -- Sum of core 5 pillars (0-10)
    total_score INTEGER NOT NULL,           -- Sum of all 7 pillars (0-14)
    meets_threshold BOOLEAN NOT NULL,       -- Does it meet 6-7/10 core + hybrid requirement?

    -- Reasoning
    reasoning TEXT NOT NULL,                -- Why each pillar scored as it did
    falsification_criteria TEXT,            -- JSON: What would prove this thesis wrong

    scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analyzed_content_id) REFERENCES analyzed_content(id) ON DELETE CASCADE
);

-- Indexes for confluence_scores
CREATE INDEX IF NOT EXISTS idx_confluence_scores_analyzed ON confluence_scores(analyzed_content_id);
CREATE INDEX IF NOT EXISTS idx_confluence_scores_total ON confluence_scores(total_score DESC);
CREATE INDEX IF NOT EXISTS idx_confluence_scores_threshold ON confluence_scores(meets_threshold);
CREATE INDEX IF NOT EXISTS idx_confluence_scores_scored_at ON confluence_scores(scored_at DESC);

-- ============================================================================
-- TABLE: themes
-- Purpose: Tracks active investment ideas being monitored
-- ============================================================================
CREATE TABLE IF NOT EXISTS themes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,              -- "Tech sector rotation", "Fed pivot imminent"
    description TEXT,

    -- Confluence tracking
    current_conviction REAL NOT NULL CHECK(current_conviction >= 0.0 AND current_conviction <= 1.0),
    confidence_interval_low REAL,
    confidence_interval_high REAL,

    -- Theme lifecycle
    first_mentioned_at TIMESTAMP,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'acted_upon', 'invalidated', 'archived')),

    -- Bayesian tracking
    prior_probability REAL,
    evidence_count INTEGER DEFAULT 0,

    json_metadata TEXT,                     -- JSON: Supporting sources, related tickers, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for themes
CREATE INDEX IF NOT EXISTS idx_themes_status ON themes(status);
CREATE INDEX IF NOT EXISTS idx_themes_conviction ON themes(current_conviction DESC);
CREATE INDEX IF NOT EXISTS idx_themes_updated_at ON themes(updated_at DESC);

-- ============================================================================
-- TABLE: theme_evidence
-- Purpose: Links analyzed content to themes (many-to-many)
-- ============================================================================
CREATE TABLE IF NOT EXISTS theme_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    theme_id INTEGER NOT NULL,
    analyzed_content_id INTEGER NOT NULL,
    supports_theme BOOLEAN DEFAULT 1,       -- False if contradicts
    evidence_strength REAL NOT NULL CHECK(evidence_strength >= 0.0 AND evidence_strength <= 1.0),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE CASCADE,
    FOREIGN KEY (analyzed_content_id) REFERENCES analyzed_content(id) ON DELETE CASCADE,
    UNIQUE(theme_id, analyzed_content_id)
);

-- Indexes for theme_evidence
CREATE INDEX IF NOT EXISTS idx_theme_evidence_theme ON theme_evidence(theme_id);
CREATE INDEX IF NOT EXISTS idx_theme_evidence_content ON theme_evidence(analyzed_content_id);
CREATE INDEX IF NOT EXISTS idx_theme_evidence_added_at ON theme_evidence(added_at DESC);

-- ============================================================================
-- TABLE: bayesian_updates
-- Purpose: Tracks how conviction changed over time for themes
-- ============================================================================
CREATE TABLE IF NOT EXISTS bayesian_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    theme_id INTEGER NOT NULL,
    prior_conviction REAL NOT NULL CHECK(prior_conviction >= 0.0 AND prior_conviction <= 1.0),
    posterior_conviction REAL NOT NULL CHECK(posterior_conviction >= 0.0 AND posterior_conviction <= 1.0),
    evidence_analyzed_content_id INTEGER,
    update_reason TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE CASCADE,
    FOREIGN KEY (evidence_analyzed_content_id) REFERENCES analyzed_content(id) ON DELETE SET NULL
);

-- Indexes for bayesian_updates
CREATE INDEX IF NOT EXISTS idx_bayesian_updates_theme ON bayesian_updates(theme_id);
CREATE INDEX IF NOT EXISTS idx_bayesian_updates_time ON bayesian_updates(updated_at DESC);

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
