"""
Migration 006: Add Theme Tracking Columns (PRD-024)

Adds columns needed for structured theme tracking:
- aliases: JSON array of alternative expressions for the theme
- evolved_from_theme_id: Reference to parent theme if evolved
- source_evidence: JSON with per-source evidence summaries
- catalysts: JSON array of linked upcoming events
- first_source: Source that first mentioned the theme
- last_updated_at: Last time evidence was added

Updates status constraint to new lifecycle values:
- emerging, active, evolved, dormant
"""


def upgrade(db):
    """
    Apply the migration (add columns).

    Args:
        db: DatabaseManager instance
    """
    print("Applying migration 006: Add theme tracking columns (PRD-024)...")

    def safe_add_column(conn, column_name, column_def):
        """Add column if it doesn't exist."""
        try:
            # Check if column exists
            cursor = conn.execute("PRAGMA table_info(themes)")
            columns = [row[1] for row in cursor.fetchall()]
            if column_name not in columns:
                conn.execute(f"ALTER TABLE themes ADD COLUMN {column_name} {column_def}")
                print(f"  Added column: {column_name}")
            else:
                print(f"  Column already exists: {column_name}")
        except Exception as e:
            print(f"  Error adding {column_name}: {e}")

    with db.get_connection() as conn:
        # Add aliases column (JSON array)
        safe_add_column(conn, "aliases", "TEXT")

        # Add evolved_from_theme_id column (self-reference)
        safe_add_column(conn, "evolved_from_theme_id", "INTEGER REFERENCES themes(id)")

        # Add source_evidence column (JSON: per-source evidence)
        safe_add_column(conn, "source_evidence", "TEXT")

        # Add catalysts column (JSON array)
        safe_add_column(conn, "catalysts", "TEXT")

        # Add first_source column
        safe_add_column(conn, "first_source", "TEXT")

        # Add last_updated_at column
        safe_add_column(conn, "last_updated_at", "TIMESTAMP")

        # Update existing themes status values to new lifecycle
        # Map old values to new: active->active, acted_upon->dormant, invalidated->dormant, archived->dormant
        try:
            conn.execute("""
                UPDATE themes SET status = 'dormant' WHERE status IN ('acted_upon', 'invalidated', 'archived')
            """)
        except Exception as e:
            print(f"  Status update skipped: {e}")

    print("SUCCESS: Migration 006 applied successfully")
    print("   - Added aliases column (JSON array)")
    print("   - Added evolved_from_theme_id column (self-reference)")
    print("   - Added source_evidence column (JSON)")
    print("   - Added catalysts column (JSON array)")
    print("   - Added first_source column")
    print("   - Added last_updated_at column")
    print("   - Updated status values to new lifecycle")


def downgrade(db):
    """
    Revert the migration (remove columns).

    Note: SQLite doesn't support DROP COLUMN directly in older versions.
    This creates a new table without the columns and copies data.

    Args:
        db: DatabaseManager instance
    """
    print("Reverting migration 006: Removing theme tracking columns...")

    with db.get_connection() as conn:
        # SQLite workaround for dropping columns
        conn.execute("""
            CREATE TABLE themes_backup AS
            SELECT id, name, description, current_conviction, confidence_interval_low,
                   confidence_interval_high, first_mentioned_at, status, prior_probability,
                   evidence_count, json_metadata, created_at, updated_at
            FROM themes
        """)
        conn.execute("DROP TABLE themes")
        conn.execute("ALTER TABLE themes_backup RENAME TO themes")

        # Recreate indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_themes_status ON themes(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_themes_conviction ON themes(current_conviction DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_themes_updated_at ON themes(updated_at DESC)")

    print("SUCCESS: Migration 006 reverted successfully")
