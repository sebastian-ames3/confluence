#!/usr/bin/env python3
"""
Database Initialization Script

Creates the SQLite database and initializes the schema.
This script will be expanded in Phase 1 (PRD-002) with the full schema.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import sqlite3

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/confluence.db")
# Extract file path from SQLite URL
DB_PATH = DATABASE_URL.replace("sqlite:///", "")


def create_database():
    """Create the database file and directory if they don't exist."""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"✓ Created database directory: {db_dir}")

    # Create database file
    conn = sqlite3.connect(DB_PATH)
    print(f"✓ Created database: {DB_PATH}")

    return conn


def init_schema(conn):
    """
    Initialize database schema.

    TODO: This will be expanded in PRD-002 with full schema:
    - sources table
    - raw_content table
    - analyzed_content table
    - confluence_scores table
    - themes table
    - theme_tracking table
    - user_actions table
    """
    cursor = conn.cursor()

    # Placeholder schema - will be replaced in Phase 1
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
    """)

    # Insert initial version
    cursor.execute("""
        INSERT OR IGNORE INTO schema_version (version, description)
        VALUES (0, 'Initial database structure')
    """)

    conn.commit()
    print("✓ Initialized schema (placeholder - will be expanded in Phase 1)")


def main():
    """Main initialization routine."""
    print("Macro Confluence Hub - Database Initialization")
    print("=" * 50)

    try:
        conn = create_database()
        init_schema(conn)
        conn.close()

        print("\n" + "=" * 50)
        print("✓ Database initialization complete!")
        print(f"  Database location: {DB_PATH}")
        print("\nNext steps:")
        print("  1. Run migrations: python scripts/run_migrations.py")
        print("  2. Seed sample data: python scripts/seed_data.py")
        print("=" * 50)

    except Exception as e:
        print(f"\n✗ Error during initialization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
