"""
Migration 001: Initial Schema

Creates all 7 core tables for the Macro Confluence Hub database.

Tables:
- sources
- raw_content
- analyzed_content
- confluence_scores
- themes
- theme_evidence
- bayesian_updates
"""

from pathlib import Path


def upgrade(db):
    """
    Apply the migration (create tables).

    Args:
        db: DatabaseManager instance
    """
    schema_file = Path("database/schema.sql")

    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    print("Applying migration 001: Initial schema...")

    # Read and execute schema.sql
    with schema_file.open('r') as f:
        schema_sql = f.read()

    with db.get_connection() as conn:
        conn.executescript(schema_sql)

    print("SUCCESS: Migration 001 applied successfully")
    print("   - Created 7 tables")
    print("   - Created all indexes")
    print("   - Foreign key constraints enabled")


def downgrade(db):
    """
    Revert the migration (drop tables).

    Args:
        db: DatabaseManager instance
    """
    print("Reverting migration 001: Dropping all tables...")

    tables = [
        "bayesian_updates",
        "theme_evidence",
        "confluence_scores",
        "analyzed_content",
        "raw_content",
        "themes",
        "sources"
    ]

    with db.get_connection() as conn:
        # Disable foreign keys temporarily
        conn.execute("PRAGMA foreign_keys = OFF")

        for table in tables:
            print(f"   - Dropping table: {table}")
            conn.execute(f"DROP TABLE IF EXISTS {table}")

        # Re-enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")

    print("SUCCESS: Migration 001 reverted successfully")
