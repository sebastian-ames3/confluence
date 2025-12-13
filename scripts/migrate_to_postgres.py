"""
SQLite to PostgreSQL Migration Script (PRD-035)

Exports data from SQLite and imports to PostgreSQL for production deployment.

Usage:
    # Export SQLite data to JSON files
    python scripts/migrate_to_postgres.py --export

    # Import JSON data to PostgreSQL
    python scripts/migrate_to_postgres.py --import

    # Verify migration (compare row counts)
    python scripts/migrate_to_postgres.py --verify

    # Full migration (export + import + verify)
    python scripts/migrate_to_postgres.py --full

Requirements:
    - SQLite database at database/confluence.db (local)
    - PostgreSQL DATABASE_URL environment variable set (for import)
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


# Tables in order (respecting foreign key dependencies)
TABLES_IN_ORDER = [
    "sources",
    "raw_content",
    "analyzed_content",
    "confluence_scores",
    "themes",
    "theme_evidence",
    "bayesian_updates",
    "syntheses",
    "service_heartbeats",
    "collection_runs"
]

EXPORT_DIR = Path("migration_export")


def export_sqlite_data():
    """Export all SQLite data to JSON files."""
    import sqlite3

    sqlite_path = os.getenv("SQLITE_PATH", "database/confluence.db")
    if not Path(sqlite_path).exists():
        print(f"SQLite database not found: {sqlite_path}")
        return False

    EXPORT_DIR.mkdir(exist_ok=True)

    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row

    total_rows = 0

    for table in TABLES_IN_ORDER:
        try:
            cursor = conn.execute(f"SELECT * FROM {table}")
            rows = [dict(row) for row in cursor.fetchall()]

            # Convert datetime strings to ISO format
            for row in rows:
                for key, value in row.items():
                    if isinstance(value, str) and "T" in value:
                        # Already ISO format
                        pass
                    elif key.endswith("_at") and value:
                        # Normalize datetime format
                        try:
                            dt = datetime.fromisoformat(value.replace(" ", "T"))
                            row[key] = dt.isoformat()
                        except ValueError:
                            pass

            export_path = EXPORT_DIR / f"{table}.json"
            with open(export_path, "w") as f:
                json.dump(rows, f, indent=2, default=str)

            print(f"Exported {table}: {len(rows)} rows")
            total_rows += len(rows)

        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                print(f"Skipped {table}: table does not exist")
            else:
                print(f"Error exporting {table}: {e}")

    conn.close()
    print(f"\nTotal exported: {total_rows} rows")
    print(f"Export directory: {EXPORT_DIR.absolute()}")
    return True


def import_to_postgres():
    """Import JSON data to PostgreSQL."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    postgres_url = os.getenv("DATABASE_URL")
    if not postgres_url:
        print("DATABASE_URL environment variable not set")
        return False

    # Fix Railway URL format
    if postgres_url.startswith("postgres://"):
        postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)

    if not EXPORT_DIR.exists():
        print(f"Export directory not found: {EXPORT_DIR}")
        print("Run with --export first")
        return False

    engine = create_engine(postgres_url)
    Session = sessionmaker(bind=engine)

    # Create tables using ORM models
    from backend.models import Base
    Base.metadata.create_all(bind=engine)
    print("Created database tables")

    total_rows = 0

    with Session() as session:
        for table in TABLES_IN_ORDER:
            export_path = EXPORT_DIR / f"{table}.json"
            if not export_path.exists():
                print(f"Skipped {table}: no export file")
                continue

            with open(export_path) as f:
                rows = json.load(f)

            if not rows:
                print(f"Skipped {table}: no data")
                continue

            try:
                # Clear existing data (for idempotent migration)
                session.execute(text(f"DELETE FROM {table}"))

                # Insert rows
                for row in rows:
                    # Handle NULL values
                    cleaned_row = {k: (v if v != "" else None) for k, v in row.items()}

                    columns = ", ".join(cleaned_row.keys())
                    placeholders = ", ".join([f":{k}" for k in cleaned_row.keys()])
                    insert_sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

                    session.execute(text(insert_sql), cleaned_row)

                session.commit()

                # Reset sequence for auto-increment
                max_id_result = session.execute(text(f"SELECT MAX(id) FROM {table}"))
                max_id = max_id_result.scalar() or 0
                if max_id > 0:
                    session.execute(text(
                        f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), {max_id})"
                    ))
                    session.commit()

                print(f"Imported {table}: {len(rows)} rows")
                total_rows += len(rows)

            except Exception as e:
                session.rollback()
                print(f"Error importing {table}: {e}")
                raise

    print(f"\nTotal imported: {total_rows} rows")
    return True


def verify_migration():
    """Verify migration by comparing row counts."""
    import sqlite3
    from sqlalchemy import create_engine, text

    sqlite_path = os.getenv("SQLITE_PATH", "database/confluence.db")
    postgres_url = os.getenv("DATABASE_URL")

    if not Path(sqlite_path).exists():
        print(f"SQLite database not found: {sqlite_path}")
        return False

    if not postgres_url:
        print("DATABASE_URL environment variable not set")
        return False

    # Fix Railway URL format
    if postgres_url.startswith("postgres://"):
        postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)

    sqlite_conn = sqlite3.connect(sqlite_path)
    pg_engine = create_engine(postgres_url)

    print("\nVerifying migration (SQLite vs PostgreSQL):\n")
    print(f"{'Table':<25} {'SQLite':<10} {'PostgreSQL':<10} {'Status'}")
    print("-" * 60)

    all_match = True

    for table in TABLES_IN_ORDER:
        # SQLite count
        sqlite_count = 0
        try:
            cursor = sqlite_conn.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            pass

        # PostgreSQL count
        pg_count = 0
        try:
            with pg_engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                pg_count = result.scalar()
        except Exception:
            pass

        status = "OK" if sqlite_count == pg_count else "MISMATCH"
        if sqlite_count != pg_count:
            all_match = False

        print(f"{table:<25} {sqlite_count:<10} {pg_count:<10} {status}")

    sqlite_conn.close()
    pg_engine.dispose()

    print("\n" + ("Migration verified successfully!" if all_match else "Migration verification FAILED - some tables have mismatched row counts"))
    return all_match


def main():
    parser = argparse.ArgumentParser(description="SQLite to PostgreSQL Migration")
    parser.add_argument("--export", action="store_true", help="Export SQLite to JSON")
    parser.add_argument("--import", dest="do_import", action="store_true", help="Import JSON to PostgreSQL")
    parser.add_argument("--verify", action="store_true", help="Verify migration")
    parser.add_argument("--full", action="store_true", help="Full migration (export + import + verify)")

    args = parser.parse_args()

    if args.full:
        print("=== Full Migration ===\n")
        print("Step 1: Export SQLite data")
        if not export_sqlite_data():
            return 1
        print("\nStep 2: Import to PostgreSQL")
        if not import_to_postgres():
            return 1
        print("\nStep 3: Verify migration")
        if not verify_migration():
            return 1
        print("\nMigration complete!")
        return 0

    if args.export:
        return 0 if export_sqlite_data() else 1

    if args.do_import:
        return 0 if import_to_postgres() else 1

    if args.verify:
        return 0 if verify_migration() else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
