#!/usr/bin/env python3
"""
Database Migration Script

Runs database migrations in sequence using Python migration files.
"""

import os
import sys
from pathlib import Path
import importlib.util

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.db import DatabaseManager


def get_applied_migrations(db):
    """
    Get list of already-applied migration numbers.

    Args:
        db: DatabaseManager instance

    Returns:
        Set of migration numbers that have been applied
    """
    # Create migrations tracking table if it doesn't exist
    with db.get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    # Get applied migrations
    result = db.execute_query("SELECT version FROM migrations ORDER BY version")
    return set(row['version'] for row in result)


def get_migration_files():
    """
    Get all migration Python files from database/migrations/.

    Returns:
        List of (version_number, file_path) tuples, sorted by version
    """
    migrations_dir = Path("database/migrations")
    if not migrations_dir.exists():
        return []

    migration_files = []
    for file_path in migrations_dir.glob("*.py"):
        if file_path.name.startswith("__"):
            continue  # Skip __init__.py, __pycache__, etc.

        # Extract version number from filename (e.g., "001_initial_schema.py" -> 1)
        try:
            version = int(file_path.stem.split('_')[0])
            migration_files.append((version, file_path))
        except (ValueError, IndexError):
            print(f"⚠️  Skipping invalid migration filename: {file_path.name}")
            continue

    return sorted(migration_files, key=lambda x: x[0])


def load_migration_module(file_path):
    """
    Dynamically load a migration module.

    Args:
        file_path: Path to migration Python file

    Returns:
        Loaded module
    """
    spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def apply_migration(db, version, file_path):
    """
    Apply a single migration.

    Args:
        db: DatabaseManager instance
        version: Migration version number
        file_path: Path to migration file
    """
    print(f"\nApplying migration {version:03d}: {file_path.name}")

    # Load migration module
    module = load_migration_module(file_path)

    if not hasattr(module, 'upgrade'):
        raise AttributeError(f"Migration {file_path.name} is missing 'upgrade' function")

    # Run upgrade
    module.upgrade(db)

    # Record migration as applied
    db.insert("migrations", {
        "version": version,
        "name": file_path.name
    })

    print(f"SUCCESS: Migration {version:03d} applied successfully")


def rollback_migration(db, version, file_path):
    """
    Roll back a single migration.

    Args:
        db: DatabaseManager instance
        version: Migration version number
        file_path: Path to migration file
    """
    print(f"\nRolling back migration {version:03d}: {file_path.name}")

    # Load migration module
    module = load_migration_module(file_path)

    if not hasattr(module, 'downgrade'):
        raise AttributeError(f"Migration {file_path.name} is missing 'downgrade' function")

    # Run downgrade
    module.downgrade(db)

    # Remove migration record
    db.delete("migrations", version)

    print(f"SUCCESS: Migration {version:03d} rolled back successfully")


def main():
    """Main migration routine."""
    import argparse

    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument(
        "--rollback",
        type=int,
        metavar="VERSION",
        help="Roll back to specific version (removes later migrations)"
    )
    parser.add_argument(
        "--db",
        default="database/confluence.db",
        help="Database path (default: database/confluence.db)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Macro Confluence Hub - Database Migrations")
    print("=" * 60)

    # Initialize database manager
    db = DatabaseManager(args.db)

    # Get migration status
    applied = get_applied_migrations(db)
    available = get_migration_files()

    if not available:
        print("\n⚠️  No migration files found in database/migrations/")
        return

    print(f"\nMigration Status:")
    print(f"  Applied: {len(applied)} migrations")
    print(f"  Available: {len(available)} migration files")

    if args.rollback is not None:
        # Rollback mode
        target_version = args.rollback
        print(f"\n🔄 Rolling back to version {target_version}")

        # Find migrations to rollback (in reverse order)
        to_rollback = [
            (v, p) for v, p in reversed(available)
            if v in applied and v > target_version
        ]

        if not to_rollback:
            print(f"\n✓ Already at version {target_version} or earlier")
            return

        print(f"\nWill rollback {len(to_rollback)} migration(s):")
        for version, file_path in to_rollback:
            print(f"  - {version:03d}: {file_path.name}")

        confirm = input("\nProceed with rollback? [y/N]: ")
        if confirm.lower() != 'y':
            print("Rollback cancelled")
            return

        for version, file_path in to_rollback:
            rollback_migration(db, version, file_path)

        print(f"\nSUCCESS: Rolled back to version {target_version}")

    else:
        # Apply pending migrations
        pending = [(v, p) for v, p in available if v not in applied]

        if not pending:
            print("\nDatabase is up to date! No pending migrations.")
            return

        print(f"\nPending migrations ({len(pending)}):")
        for version, file_path in pending:
            print(f"  - {version:03d}: {file_path.name}")

        confirm = input("\nApply pending migrations? [Y/n]: ")
        if confirm.lower() == 'n':
            print("Migration cancelled")
            return

        for version, file_path in pending:
            apply_migration(db, version, file_path)

        print(f"\nSUCCESS: All migrations applied successfully!")

    print("=" * 60)


if __name__ == "__main__":
    main()
