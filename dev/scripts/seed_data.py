#!/usr/bin/env python3
"""
Database Seeding Script

Populates the database with sample data for development and testing.
This script will be expanded in Phase 1 (PRD-002) with realistic test data.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import sqlite3
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/confluence.db")
DB_PATH = DATABASE_URL.replace("sqlite:///", "")


def seed_sample_data(conn):
    """
    Seed the database with sample data.

    TODO: In Phase 1 (PRD-002), this will populate:
    - Sample sources (42macro, Discord, etc.)
    - Sample raw content items
    - Sample analyzed content with confluence scores
    - Sample themes and tracking data
    - Sample user actions

    This allows development and testing without live API credentials.
    """
    cursor = conn.cursor()

    # Placeholder - no actual data yet
    print("✓ Sample data seeding prepared (will be implemented in Phase 1)")
    print("  Future data will include:")
    print("    - Sample research reports from each source")
    print("    - Pre-analyzed content with confluence scores")
    print("    - Example investment themes over time")
    print("    - Sample Bayesian tracking data")

    conn.commit()


def main():
    """Main seeding routine."""
    print("Macro Confluence Hub - Database Seeding")
    print("=" * 50)

    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"✗ Database not found: {DB_PATH}")
        print("  Run 'python scripts/init_database.py' first")
        sys.exit(1)

    try:
        conn = sqlite3.connect(DB_PATH)
        print(f"Connected to database: {DB_PATH}")

        # Seed data
        seed_sample_data(conn)

        conn.close()

        print("\n" + "=" * 50)
        print("✓ Database seeding complete!")
        print("\nNext steps:")
        print("  1. Start the backend: uvicorn backend.app:app --reload")
        print("  2. Open the dashboard in your browser")
        print("=" * 50)

    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
