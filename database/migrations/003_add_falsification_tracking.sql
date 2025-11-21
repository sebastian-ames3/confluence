-- ============================================================================
-- Migration: Add Falsification Tracking to Themes
-- Purpose: Track when falsification criteria are triggered
-- Date: 2025-11-21
-- ============================================================================

-- Add falsification tracking columns to themes table
ALTER TABLE themes ADD COLUMN is_falsified BOOLEAN DEFAULT 0;
ALTER TABLE themes ADD COLUMN falsification_status TEXT; -- JSON: Details about falsification events
ALTER TABLE themes ADD COLUMN falsification_triggered_at TIMESTAMP;

-- Create index for quick filtering of falsified themes
CREATE INDEX IF NOT EXISTS idx_themes_falsified ON themes(is_falsified);

-- Comments for clarity
-- is_falsified: Boolean flag indicating if any falsification criterion has been met
-- falsification_status: JSON storing details like:
--   {
--     "triggered_criteria": ["VIX > 25", "SPX < 4000"],
--     "trigger_times": ["2025-01-15T10:30:00", "2025-01-16T09:45:00"],
--     "notes": "Multiple criteria violated"
--   }
-- falsification_triggered_at: Timestamp of first falsification event
