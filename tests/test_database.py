"""
Tests for Database utilities
"""
import pytest
from backend.utils.db import DatabaseManager, get_db


class TestDatabaseManager:
    """Test suite for DatabaseManager."""

    def test_get_db_singleton(self):
        """Test that get_db returns singleton."""
        db1 = get_db()
        db2 = get_db()

        # Should be the same instance
        assert db1 is db2

    def test_database_connection(self):
        """Test that database connection works."""
        db = get_db()

        # Should be able to execute a simple query
        result = db.execute_query("SELECT 1 as test", fetch="one")
        assert result is not None

    def test_wal_mode_enabled(self):
        """Test that WAL mode is enabled."""
        db = get_db()

        # Check journal mode
        result = db.execute_query("PRAGMA journal_mode", fetch="one")

        # Should be WAL (or wal)
        assert result is not None
        # Extract the actual value from the Row object
        journal_mode = str(result[0]).lower() if hasattr(result, '__getitem__') else str(result).lower()
        assert "wal" in journal_mode
