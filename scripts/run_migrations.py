#!/usr/bin/env python3
"""
Database Migration Script

Runs database migrations in sequence.
This script will be expanded in Phase 1 (PRD-002) with actual migrations.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import sqlite3
from datetime import datetime

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/confluence.db")
DB_PATH = DATABASE_URL.replace("sqlite:///", "")
MIGRATIONS_DIR = "database/migrations"


def get_current_version(conn):
    """Get the current schema version."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MAX(version) FROM schema_version")
        result = cursor.fetchone()
        return result[0] if result[0] is not None else 0
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return 0


def get_pending_migrations():
    """
    Get list of pending migration files.

    TODO: In Phase 1, this will scan database/migrations/ for .sql files
    and return those not yet applied.
    """
    # Placeholder - no migrations yet
    return []


def apply_migration(conn, migration_file, version):
    """Apply a single migration file."""
    cursor = conn.cursor()

    # Read and execute migration
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
        cursor.executescript(migration_sql)

    # Update schema version
    cursor.execute("""
        INSERT INTO schema_version (version, description)
        VALUES (?, ?)
    """, (version, f"Applied migration: {os.path.basename(migration_file)}"))

    conn.commit()
    print(f"✓ Applied migration {version}: {os.path.basename(migration_file)}")


def main():
    """Main migration routine."""
    print("Macro Confluence Hub - Database Migrations")
    print("=" * 50)

    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"✗ Database not found: {DB_PATH}")
        print("  Run 'python scripts/init_database.py' first")
        sys.exit(1)

    try:
        conn = sqlite3.connect(DB_PATH)
        current_version = get_current_version(conn)
        print(f"Current schema version: {current_version}")

        # Get pending migrations
        pending = get_pending_migrations()

        if not pending:
            print("\n✓ No pending migrations. Database is up to date!")
        else:
            print(f"\nFound {len(pending)} pending migration(s):")
            for migration_file, version in pending:
                apply_migration(conn, migration_file, version)

            print("\n✓ All migrations applied successfully!")

        conn.close()

        print("=" * 50)

    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
