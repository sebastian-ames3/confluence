"""
Database utilities for Macro Confluence Hub.

Provides database connection management, CRUD operations, and query utilities.

DEPRECATED (PRD-035): This module uses raw SQLite queries and is being replaced
by SQLAlchemy ORM with async sessions. Use backend.models instead:
- For sync sessions: from backend.models import get_db, SessionLocal
- For async sessions: from backend.models import get_async_db, AsyncSessionLocal
"""
import sqlite3
import json
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


class DatabaseManager:
    """
    DEPRECATED: Manages database connections using raw SQLite queries.

    This class is deprecated as of PRD-035. Use SQLAlchemy ORM instead:
    - backend.models.get_db() for sync sessions
    - backend.models.get_async_db() for async sessions
    """

    def __init__(self, db_path: str = "database/confluence.db"):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        warnings.warn(
            "DatabaseManager is deprecated. Use backend.models with SQLAlchemy ORM instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.db_path = db_path
        self._ensure_database_exists()

    def _ensure_database_exists(self):
        """Create database directory if it doesn't exist."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Yields:
            sqlite3.Connection: Database connection

        Example:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM sources")
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
        conn.execute("PRAGMA journal_mode=WAL")  # Enable Write-Ahead Logging for concurrent access
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch: str = "all"
    ) -> List[sqlite3.Row]:
        """
        Execute a SQL query and return results.

        Args:
            query: SQL query string
            params: Query parameters (prevents SQL injection)
            fetch: "all", "one", or "none"

        Returns:
            Query results as list of Row objects

        Example:
            results = db.execute_query(
                "SELECT * FROM sources WHERE active = ?",
                (1,),
                fetch="all"
            )
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if fetch == "all":
                return cursor.fetchall()
            elif fetch == "one":
                return cursor.fetchone()
            else:
                return []

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        Insert a row into a table.

        Args:
            table: Table name
            data: Dictionary of column: value pairs

        Returns:
            ID of inserted row

        Example:
            source_id = db.insert("sources", {
                "name": "42macro",
                "type": "web",
                "active": True
            })
        """
        # Convert boolean values
        data = self._prepare_data(data)

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(data.values()))
            return cursor.lastrowid

    def update(self, table: str, id: int, data: Dict[str, Any]) -> bool:
        """
        Update a row in a table.

        Args:
            table: Table name
            id: Row ID
            data: Dictionary of column: value pairs to update

        Returns:
            True if update successful

        Example:
            db.update("sources", 1, {"active": False})
        """
        # Convert boolean values
        data = self._prepare_data(data)

        # Add updated_at only if column exists in table and not already in data
        if "updated_at" not in data:
            table_columns = [col["name"] for col in self.get_table_info(table)]
            if "updated_at" in table_columns:
                data["updated_at"] = datetime.now().isoformat()

        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE id = ?"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(data.values()) + (id,))
            return cursor.rowcount > 0

    def delete(self, table: str, id: int) -> bool:
        """
        Delete a row from a table.

        Args:
            table: Table name
            id: Row ID

        Returns:
            True if delete successful

        Example:
            db.delete("raw_content", 42)
        """
        query = f"DELETE FROM {table} WHERE id = ?"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id,))
            return cursor.rowcount > 0

    def select(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[sqlite3.Row]:
        """
        Select rows from a table with optional filters.

        Args:
            table: Table name
            filters: Dictionary of column: value pairs for WHERE clause
            order_by: Column name to order by (prefix with '-' for DESC)
            limit: Maximum number of rows to return

        Returns:
            List of matching rows

        Example:
            active_sources = db.select(
                "sources",
                filters={"active": True},
                order_by="-updated_at",
                limit=10
            )
        """
        query = f"SELECT * FROM {table}"
        params = []

        if filters:
            where_clauses = []
            for key, value in filters.items():
                where_clauses.append(f"{key} = ?")
                params.append(value)
            query += " WHERE " + " AND ".join(where_clauses)

        if order_by:
            if order_by.startswith("-"):
                query += f" ORDER BY {order_by[1:]} DESC"
            else:
                query += f" ORDER BY {order_by}"

        if limit:
            query += f" LIMIT {limit}"

        return self.execute_query(query, tuple(params) if params else None)

    def _prepare_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare data for database insertion.

        Converts:
        - Booleans to integers (SQLite doesn't have native boolean)
        - Dicts/lists to JSON strings

        Args:
            data: Dictionary of data

        Returns:
            Prepared data dictionary
        """
        prepared = {}
        for key, value in data.items():
            if isinstance(value, bool):
                prepared[key] = 1 if value else 0
            elif isinstance(value, (dict, list)):
                prepared[key] = json.dumps(value)
            elif value is None:
                prepared[key] = None
            else:
                prepared[key] = value
        return prepared

    def row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        Convert a Row object to a dictionary.

        Args:
            row: sqlite3.Row object

        Returns:
            Dictionary with column names as keys

        Example:
            row = db.execute_query("SELECT * FROM sources WHERE id = 1", fetch="one")
            data = db.row_to_dict(row)
        """
        if row is None:
            return {}
        return dict(row)

    def initialize_schema(self, schema_file: str = "database/schema.sql"):
        """
        Initialize database with schema from SQL file.

        Args:
            schema_file: Path to schema.sql file

        Example:
            db.initialize_schema()
        """
        schema_path = Path(schema_file)
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")

        with schema_path.open('r') as f:
            schema_sql = f.read()

        with self.get_connection() as conn:
            conn.executescript(schema_sql)

    def get_table_info(self, table: str) -> List[Dict[str, Any]]:
        """
        Get column information for a table.

        Args:
            table: Table name

        Returns:
            List of column info dictionaries

        Example:
            columns = db.get_table_info("sources")
        """
        query = f"PRAGMA table_info({table})"
        rows = self.execute_query(query)
        return [self.row_to_dict(row) for row in rows]

    def vacuum(self):
        """
        Run VACUUM to optimize database file size.

        Example:
            db.vacuum()
        """
        with self.get_connection() as conn:
            conn.execute("VACUUM")


def get_or_create_source(db_session, source_name: str):
    """
    Get existing source by name or create if doesn't exist.

    Args:
        db_session: SQLAlchemy database session
        source_name: Name of the source (e.g., "youtube", "42macro")

    Returns:
        Source object

    Example:
        from backend.models import SessionLocal
        from backend.utils.db import get_or_create_source

        db = SessionLocal()
        source = get_or_create_source(db, "youtube")
    """
    from backend.models import Source

    # Try to find existing source
    source = db_session.query(Source).filter(Source.name == source_name).first()

    if source:
        return source

    # Create new source
    source = Source(
        name=source_name,
        type="api" if source_name in ["youtube", "twitter"] else "web",
        active=True
    )
    db_session.add(source)
    db_session.commit()

    return source


# Singleton instance
_db_instance = None


def get_db(db_path: str = "database/confluence.db") -> DatabaseManager:
    """
    Get database manager singleton instance.

    Args:
        db_path: Path to database file

    Returns:
        DatabaseManager instance

    Example:
        from backend.utils.db import get_db

        db = get_db()
        sources = db.select("sources")
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager(db_path)
    return _db_instance
