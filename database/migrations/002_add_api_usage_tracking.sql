-- ============================================================================
-- Migration: Add API Usage Tracking Table
-- Purpose: Track daily API usage to prevent cost explosions
-- Date: 2025-11-21
-- ============================================================================

-- Table for tracking API usage limits
CREATE TABLE IF NOT EXISTS api_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,                  -- YYYY-MM-DD format
    vision_analyses INTEGER DEFAULT 0,          -- Count of Claude Vision API calls
    transcript_analyses INTEGER DEFAULT 0,      -- Count of Whisper API calls
    text_analyses INTEGER DEFAULT 0,            -- Count of standard Claude API calls
    estimated_cost_usd REAL DEFAULT 0.0,        -- Estimated cost for the day
    notes TEXT,                                 -- Any notes about unusual usage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for quick date lookup
CREATE INDEX IF NOT EXISTS idx_api_usage_date ON api_usage(date DESC);
