"""
Migration 004: Add Syntheses and Collection Runs Tables

Creates tables for:
- syntheses: AI-generated research synthesis summaries
- collection_runs: Tracks collection runs for status display

Part of PRD-012: Dashboard Simplification & Synthesis Agent
"""


def upgrade(db):
    """
    Apply the migration (create tables).

    Args:
        db: DatabaseManager instance
    """
    print("Applying migration 004: Add syntheses and collection_runs tables...")

    with db.get_connection() as conn:
        # Create syntheses table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS syntheses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- Synthesis content
                synthesis TEXT NOT NULL,
                key_themes TEXT,
                high_conviction_ideas TEXT,
                contradictions TEXT,
                market_regime TEXT,
                catalysts TEXT,

                -- Metadata
                time_window TEXT NOT NULL,
                content_count INTEGER NOT NULL DEFAULT 0,
                sources_included TEXT,

                -- Optional focus
                focus_topic TEXT,

                -- Cost tracking
                token_usage INTEGER,

                -- Timestamps
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for syntheses
        conn.execute("CREATE INDEX IF NOT EXISTS idx_syntheses_time_window ON syntheses(time_window)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_syntheses_generated_at ON syntheses(generated_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_syntheses_focus_topic ON syntheses(focus_topic)")

        # Create collection_runs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS collection_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                -- Run metadata
                run_type TEXT NOT NULL,
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,

                -- Results per source (JSON object)
                source_results TEXT,

                -- Totals
                total_items_collected INTEGER DEFAULT 0,
                successful_sources INTEGER DEFAULT 0,
                failed_sources INTEGER DEFAULT 0,

                -- Error tracking
                errors TEXT,

                -- Status
                status TEXT DEFAULT 'running' CHECK(status IN ('running', 'completed', 'failed'))
            )
        """)

        # Create indexes for collection_runs
        conn.execute("CREATE INDEX IF NOT EXISTS idx_collection_runs_started_at ON collection_runs(started_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_collection_runs_status ON collection_runs(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_collection_runs_type ON collection_runs(run_type)")

    print("SUCCESS: Migration 004 applied successfully")
    print("   - Created syntheses table")
    print("   - Created collection_runs table")
    print("   - Created indexes")


def downgrade(db):
    """
    Revert the migration (drop tables).

    Args:
        db: DatabaseManager instance
    """
    print("Reverting migration 004: Dropping syntheses and collection_runs tables...")

    with db.get_connection() as conn:
        conn.execute("DROP TABLE IF EXISTS syntheses")
        conn.execute("DROP TABLE IF EXISTS collection_runs")

    print("SUCCESS: Migration 004 reverted successfully")
