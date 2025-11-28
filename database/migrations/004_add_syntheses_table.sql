-- ============================================================================
-- Migration 004: Add syntheses table
-- ============================================================================
-- Date: 2025-11-28
-- Description: Adds table for storing AI-generated research synthesis
-- PRD: PRD-012 (Dashboard Simplification & Synthesis Agent)
-- ============================================================================

-- ============================================================================
-- TABLE: syntheses
-- Purpose: Stores AI-generated research synthesis summaries
-- ============================================================================
CREATE TABLE IF NOT EXISTS syntheses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Synthesis content
    synthesis TEXT NOT NULL,                  -- 1-3 paragraph natural language synthesis
    key_themes TEXT,                          -- JSON array of key themes
    high_conviction_ideas TEXT,               -- JSON array of high-conviction ideas
    contradictions TEXT,                      -- JSON array of contradictions
    market_regime TEXT,                       -- "risk-on", "risk-off", "transitioning", "unclear"
    catalysts TEXT,                           -- JSON array of upcoming catalysts

    -- Metadata
    time_window TEXT NOT NULL,                -- "24h", "7d", "30d"
    content_count INTEGER NOT NULL DEFAULT 0, -- Number of content items analyzed
    sources_included TEXT,                    -- JSON array of sources used

    -- Optional focus
    focus_topic TEXT,                         -- If synthesis was topic-focused

    -- Cost tracking
    token_usage INTEGER,                      -- Tokens used for generation

    -- Timestamps
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for syntheses
CREATE INDEX IF NOT EXISTS idx_syntheses_time_window ON syntheses(time_window);
CREATE INDEX IF NOT EXISTS idx_syntheses_generated_at ON syntheses(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_syntheses_focus_topic ON syntheses(focus_topic);

-- ============================================================================
-- TABLE: collection_runs
-- Purpose: Tracks collection runs for status display
-- ============================================================================
CREATE TABLE IF NOT EXISTS collection_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Run metadata
    run_type TEXT NOT NULL,                   -- "scheduled_6am", "scheduled_6pm", "manual"
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,

    -- Results per source (JSON object)
    source_results TEXT,                      -- {"youtube": {"status": "success", "count": 5}, ...}

    -- Totals
    total_items_collected INTEGER DEFAULT 0,
    successful_sources INTEGER DEFAULT 0,
    failed_sources INTEGER DEFAULT 0,

    -- Error tracking
    errors TEXT,                              -- JSON array of errors

    -- Status
    status TEXT DEFAULT 'running' CHECK(status IN ('running', 'completed', 'failed'))
);

-- Indexes for collection_runs
CREATE INDEX IF NOT EXISTS idx_collection_runs_started_at ON collection_runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_collection_runs_status ON collection_runs(status);
CREATE INDEX IF NOT EXISTS idx_collection_runs_type ON collection_runs(run_type);

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
