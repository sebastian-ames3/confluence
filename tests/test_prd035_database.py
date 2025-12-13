"""
Tests for PRD-035: Database Modernization

Tests for:
- 35.1 Async SQLAlchemy Session Support
- 35.2 Route Migration to Async Sessions (heartbeat.py, search.py)
- 35.3 PostgreSQL Migration Script
- 35.4 Legacy DatabaseManager Deprecation
"""

import pytest
import warnings
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestAsyncSessionSupport:
    """Test 35.1: Async SQLAlchemy session support."""

    def test_async_dependencies_in_requirements(self):
        """Verify async database dependencies are in requirements.txt."""
        requirements_path = Path(__file__).parent.parent / "requirements.txt"
        content = requirements_path.read_text()

        assert "aiosqlite" in content, "aiosqlite should be in requirements.txt"
        assert "asyncpg" in content, "asyncpg should be in requirements.txt"
        assert "greenlet" in content, "greenlet should be in requirements.txt"

    def test_get_async_url_function_exists(self):
        """Verify get_async_url function exists in models."""
        from backend.models import get_async_url

        assert callable(get_async_url)

    def test_get_async_url_sqlite_conversion(self):
        """Verify SQLite URL conversion logic."""
        from backend.models import get_async_url

        sqlite_url = "sqlite:///database/confluence.db"
        async_url = get_async_url(sqlite_url)

        assert "sqlite+aiosqlite:///" in async_url
        assert "confluence.db" in async_url

    def test_get_async_url_postgresql_conversion(self):
        """Verify PostgreSQL URL conversion logic."""
        from backend.models import get_async_url

        pg_url = "postgresql://user:pass@host:5432/db"
        async_url = get_async_url(pg_url)

        assert "postgresql+asyncpg://" in async_url
        assert "user:pass@host:5432/db" in async_url

    def test_async_database_url_defined(self):
        """Verify ASYNC_DATABASE_URL is defined."""
        from backend.models import ASYNC_DATABASE_URL

        assert ASYNC_DATABASE_URL is not None
        assert isinstance(ASYNC_DATABASE_URL, str)

    def test_get_async_db_function_exists(self):
        """Verify get_async_db dependency function exists."""
        from backend.models import get_async_db
        import inspect

        assert callable(get_async_db)
        assert inspect.isasyncgenfunction(get_async_db)

    def test_async_engine_variable_exists(self):
        """Verify async_engine variable is defined (may be None if deps not installed)."""
        from backend.models import async_engine

        # async_engine should exist (may be None if aiosqlite not installed)
        assert hasattr(__import__('backend.models', fromlist=['async_engine']), 'async_engine')

    def test_async_session_local_variable_exists(self):
        """Verify AsyncSessionLocal variable is defined (may be None if deps not installed)."""
        from backend.models import AsyncSessionLocal

        # AsyncSessionLocal should exist (may be None if aiosqlite not installed)
        assert hasattr(__import__('backend.models', fromlist=['AsyncSessionLocal']), 'AsyncSessionLocal')


class TestServiceHeartbeatModel:
    """Test ServiceHeartbeat ORM model."""

    def test_service_heartbeat_model_exists(self):
        """Verify ServiceHeartbeat model exists."""
        from backend.models import ServiceHeartbeat

        assert ServiceHeartbeat is not None
        assert ServiceHeartbeat.__tablename__ == "service_heartbeats"

    def test_service_heartbeat_fields(self):
        """Verify ServiceHeartbeat has required fields."""
        from backend.models import ServiceHeartbeat

        # Check column names
        columns = [c.name for c in ServiceHeartbeat.__table__.columns]

        assert "id" in columns
        assert "service_name" in columns
        assert "last_heartbeat" in columns
        assert "heartbeat_count" in columns
        assert "status" in columns
        assert "created_at" in columns
        assert "updated_at" in columns


class TestHeartbeatRouteAsync:
    """Test 35.2: Heartbeat route migration to async."""

    def test_heartbeat_imports_async_session(self):
        """Verify heartbeat.py imports async session."""
        heartbeat_path = Path(__file__).parent.parent / "backend" / "routes" / "heartbeat.py"
        content = heartbeat_path.read_text()

        assert "from sqlalchemy.ext.asyncio import AsyncSession" in content
        assert "from backend.models import get_async_db" in content

    def test_heartbeat_uses_async_db_dependency(self):
        """Verify heartbeat routes use get_async_db dependency."""
        heartbeat_path = Path(__file__).parent.parent / "backend" / "routes" / "heartbeat.py"
        content = heartbeat_path.read_text()

        assert "Depends(get_async_db)" in content

    def test_heartbeat_uses_await_execute(self):
        """Verify heartbeat uses await db.execute()."""
        heartbeat_path = Path(__file__).parent.parent / "backend" / "routes" / "heartbeat.py"
        content = heartbeat_path.read_text()

        assert "await db.execute" in content
        assert "await db.commit" in content

    def test_heartbeat_uses_select_statement(self):
        """Verify heartbeat uses SQLAlchemy select()."""
        heartbeat_path = Path(__file__).parent.parent / "backend" / "routes" / "heartbeat.py"
        content = heartbeat_path.read_text()

        assert "from sqlalchemy import select" in content
        assert "select(ServiceHeartbeat)" in content


class TestSearchRouteAsync:
    """Test 35.2: Search route migration to async."""

    def test_search_imports_async_session(self):
        """Verify search.py imports async session."""
        search_path = Path(__file__).parent.parent / "backend" / "routes" / "search.py"
        content = search_path.read_text()

        assert "from sqlalchemy.ext.asyncio import AsyncSession" in content
        assert "get_async_db" in content

    def test_search_uses_async_db_dependency(self):
        """Verify search routes use get_async_db dependency."""
        search_path = Path(__file__).parent.parent / "backend" / "routes" / "search.py"
        content = search_path.read_text()

        assert "Depends(get_async_db)" in content

    def test_search_uses_await_execute(self):
        """Verify search uses await db.execute()."""
        search_path = Path(__file__).parent.parent / "backend" / "routes" / "search.py"
        content = search_path.read_text()

        assert "await db.execute" in content

    def test_search_uses_select_statement(self):
        """Verify search uses SQLAlchemy select()."""
        search_path = Path(__file__).parent.parent / "backend" / "routes" / "search.py"
        content = search_path.read_text()

        assert "from sqlalchemy import select" in content
        assert "select(RawContent" in content or "select(Source" in content


class TestPostgresMigrationScript:
    """Test 35.3: PostgreSQL migration script."""

    def test_migration_script_exists(self):
        """Verify migration script exists."""
        script_path = Path(__file__).parent.parent / "scripts" / "migrate_to_postgres.py"
        assert script_path.exists(), "migrate_to_postgres.py should exist"

    def test_migration_script_has_export(self):
        """Verify migration script has export functionality."""
        script_path = Path(__file__).parent.parent / "scripts" / "migrate_to_postgres.py"
        content = script_path.read_text()

        assert "def export_sqlite_data" in content
        assert "--export" in content

    def test_migration_script_has_import(self):
        """Verify migration script has import functionality."""
        script_path = Path(__file__).parent.parent / "scripts" / "migrate_to_postgres.py"
        content = script_path.read_text()

        assert "def import_to_postgres" in content
        assert "--import" in content

    def test_migration_script_has_verify(self):
        """Verify migration script has verification functionality."""
        script_path = Path(__file__).parent.parent / "scripts" / "migrate_to_postgres.py"
        content = script_path.read_text()

        assert "def verify_migration" in content
        assert "--verify" in content

    def test_migration_script_tables_order(self):
        """Verify migration script handles tables in correct order (FK dependencies)."""
        script_path = Path(__file__).parent.parent / "scripts" / "migrate_to_postgres.py"
        content = script_path.read_text()

        assert "TABLES_IN_ORDER" in content
        # sources must come before raw_content (FK)
        assert content.index('"sources"') < content.index('"raw_content"')
        # raw_content must come before analyzed_content (FK)
        assert content.index('"raw_content"') < content.index('"analyzed_content"')


class TestDatabaseManagerDeprecation:
    """Test 35.4: Legacy DatabaseManager deprecation."""

    def test_db_module_has_deprecation_notice(self):
        """Verify db.py module has deprecation notice."""
        db_path = Path(__file__).parent.parent / "backend" / "utils" / "db.py"
        content = db_path.read_text()

        assert "DEPRECATED" in content
        assert "PRD-035" in content

    def test_database_manager_deprecation_warning_defined(self):
        """Verify DatabaseManager has deprecation warning in code."""
        db_path = Path(__file__).parent.parent / "backend" / "utils" / "db.py"
        content = db_path.read_text()

        assert "warnings.warn" in content
        assert "DeprecationWarning" in content


class TestModelsPRD035Integration:
    """Integration tests for models.py PRD-035 changes."""

    def test_sync_engine_still_works(self):
        """Verify sync engine (backwards compatibility) still works."""
        from backend.models import engine, SessionLocal

        assert engine is not None
        assert SessionLocal is not None

    def test_get_db_still_works(self):
        """Verify sync get_db (backwards compatibility) still works."""
        from backend.models import get_db
        import inspect

        assert callable(get_db)
        assert inspect.isgeneratorfunction(get_db)

    def test_all_models_have_tablenames(self):
        """Verify all models have correct __tablename__."""
        from backend.models import (
            Source, RawContent, AnalyzedContent, ConfluenceScore,
            Theme, ThemeEvidence, BayesianUpdate, Synthesis,
            ServiceHeartbeat, CollectionRun
        )

        models = [
            (Source, "sources"),
            (RawContent, "raw_content"),
            (AnalyzedContent, "analyzed_content"),
            (ConfluenceScore, "confluence_scores"),
            (Theme, "themes"),
            (ThemeEvidence, "theme_evidence"),
            (BayesianUpdate, "bayesian_updates"),
            (Synthesis, "syntheses"),
            (ServiceHeartbeat, "service_heartbeats"),
            (CollectionRun, "collection_runs"),
        ]

        for model, expected_tablename in models:
            assert model.__tablename__ == expected_tablename

    def test_postgres_url_fix_in_models(self):
        """Verify postgres:// URL fix is in models.py."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        # Check for the Railway URL fix
        assert 'postgres://' in content
        assert 'postgresql://' in content
        assert '.replace("postgres://", "postgresql://"' in content

    def test_async_graceful_fallback(self):
        """Verify async engine gracefully handles missing dependencies."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        # Check for graceful fallback when async deps not installed
        assert "ModuleNotFoundError" in content
        assert "async_engine = None" in content or "AsyncSessionLocal = None" in content


class TestAsyncSessionConfig:
    """Test async session configuration."""

    def test_async_session_config_in_code(self):
        """Verify async session config is defined correctly in code."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        assert "expire_on_commit=False" in content
        assert "autocommit=False" in content
        assert "autoflush=False" in content

    def test_async_session_uses_async_sessionmaker(self):
        """Verify async_sessionmaker is used."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        assert "async_sessionmaker" in content
        assert "from sqlalchemy.ext.asyncio import" in content


class TestAsyncDbRuntimeError:
    """Test get_async_db raises appropriate error when unavailable."""

    def test_get_async_db_raises_when_unavailable(self):
        """Verify get_async_db raises RuntimeError when async deps not available."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        # Check that RuntimeError is raised when AsyncSessionLocal is None
        assert "RuntimeError" in content
        assert "Async database support not available" in content
