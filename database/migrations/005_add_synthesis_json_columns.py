"""
Migration 005: Add V2/V3 Synthesis JSON Columns

Adds columns needed to persist v2/v3 synthesis data:
- schema_version: Version identifier (1.0, 2.0, 3.0)
- synthesis_json: Full JSON for v2/v3 synthesis (confluence zones, priorities, etc.)

Without these columns, v2/v3 syntheses display correctly on generation
but disappear on page reload because they can't be loaded from the database.
"""


def upgrade(db):
    """
    Apply the migration (add columns).

    Args:
        db: DatabaseManager instance
    """
    print("Applying migration 005: Add schema_version and synthesis_json columns...")

    with db.get_connection() as conn:
        # Add schema_version column
        conn.execute("""
            ALTER TABLE syntheses ADD COLUMN schema_version VARCHAR(10) DEFAULT '1.0'
        """)

        # Add synthesis_json column for full v2/v3 data
        conn.execute("""
            ALTER TABLE syntheses ADD COLUMN synthesis_json TEXT
        """)

    print("SUCCESS: Migration 005 applied successfully")
    print("   - Added schema_version column (default '1.0')")
    print("   - Added synthesis_json column for v2/v3 synthesis data")


def downgrade(db):
    """
    Revert the migration (remove columns).

    Note: SQLite doesn't support DROP COLUMN directly in older versions.
    This creates a new table without the columns and copies data.

    Args:
        db: DatabaseManager instance
    """
    print("Reverting migration 005: Removing schema_version and synthesis_json columns...")

    with db.get_connection() as conn:
        # SQLite workaround for dropping columns
        conn.execute("""
            CREATE TABLE syntheses_backup AS
            SELECT id, synthesis, key_themes, high_conviction_ideas, contradictions,
                   market_regime, catalysts, time_window, content_count, sources_included,
                   focus_topic, token_usage, generated_at
            FROM syntheses
        """)
        conn.execute("DROP TABLE syntheses")
        conn.execute("ALTER TABLE syntheses_backup RENAME TO syntheses")

        # Recreate indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_syntheses_time_window ON syntheses(time_window)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_syntheses_generated_at ON syntheses(generated_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_syntheses_focus_topic ON syntheses(focus_topic)")

    print("SUCCESS: Migration 005 reverted successfully")
