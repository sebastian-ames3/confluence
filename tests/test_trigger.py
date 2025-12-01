"""
Tests for Trigger API endpoints

Part of PRD-014: Deployment & Infrastructure Fixes
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

# Set test API key before importing app
os.environ["TRIGGER_API_KEY"] = "test-api-key-12345"

from backend.app import app
from backend.models import CollectionRun


@pytest.fixture
def client():
    """Provide a test client."""
    return TestClient(app)


@pytest.fixture
def valid_api_key():
    """Return valid API key for tests."""
    return "test-api-key-12345"


@pytest.fixture
def mock_db_session():
    """Provide a mock database session."""
    session = MagicMock()
    return session


class TestAPIKeyAuthentication:
    """Test API key authentication."""

    def test_missing_api_key_returns_401(self, client):
        """Test that missing API key returns 401."""
        response = client.post("/api/trigger/collect")
        assert response.status_code == 401
        assert "Missing API key" in response.json()["detail"]

    def test_invalid_api_key_returns_401(self, client):
        """Test that invalid API key returns 401."""
        response = client.post(
            "/api/trigger/collect",
            headers={"X-API-Key": "wrong-key"}
        )
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    def test_valid_api_key_passes_auth(self, client, valid_api_key):
        """Test that valid API key passes authentication."""
        # This will fail at the collector level but proves auth passes
        with patch('backend.routes.trigger.get_db') as mock_get_db:
            mock_session = MagicMock()
            mock_run = MagicMock(spec=CollectionRun)
            mock_run.id = 1
            mock_session.add = MagicMock()
            mock_session.commit = MagicMock()
            mock_session.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', 1))
            mock_get_db.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

            # Use the generator mock pattern for FastAPI dependency
            def mock_db_generator():
                yield mock_session

            with patch('backend.routes.trigger.get_db', mock_db_generator):
                response = client.post(
                    "/api/trigger/collect",
                    headers={"X-API-Key": valid_api_key},
                    json={"run_type": "manual"}
                )

            # Should not be 401
            assert response.status_code != 401

    def test_development_mode_allows_no_key(self, client):
        """Test that development mode allows requests without key when env var not set."""
        # Temporarily remove the API key
        original_key = os.environ.get("TRIGGER_API_KEY")
        del os.environ["TRIGGER_API_KEY"]

        try:
            with patch('backend.routes.trigger.get_db') as mock_get_db:
                def mock_db_generator():
                    mock_session = MagicMock()
                    yield mock_session

                with patch('backend.routes.trigger.get_db', mock_db_generator):
                    response = client.post(
                        "/api/trigger/collect",
                        json={"run_type": "manual"}
                    )

                # Should not be 401 in development mode
                assert response.status_code != 401
        finally:
            # Restore the API key
            if original_key:
                os.environ["TRIGGER_API_KEY"] = original_key


class TestCollectEndpoint:
    """Test /api/trigger/collect endpoint."""

    def test_collect_accepts_valid_request(self, client, valid_api_key):
        """Test that collect endpoint accepts valid requests."""
        with patch('backend.routes.trigger.get_db') as mock_get_db:
            mock_session = MagicMock()

            # Mock the CollectionRun creation
            def refresh_mock(obj):
                obj.id = 123

            mock_session.refresh = refresh_mock

            def mock_db_generator():
                yield mock_session

            with patch('backend.routes.trigger.get_db', mock_db_generator):
                with patch('backend.routes.trigger._run_collection_job') as mock_run:
                    response = client.post(
                        "/api/trigger/collect",
                        headers={"X-API-Key": valid_api_key},
                        json={"run_type": "scheduled_6am", "sources": ["youtube"]}
                    )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "accepted"
            assert "job_id" in data
            assert "youtube" in data["sources"]

    def test_collect_invalid_sources_returns_400(self, client, valid_api_key):
        """Test that invalid sources return 400."""
        with patch('backend.routes.trigger.get_db') as mock_get_db:
            mock_session = MagicMock()

            def mock_db_generator():
                yield mock_session

            with patch('backend.routes.trigger.get_db', mock_db_generator):
                response = client.post(
                    "/api/trigger/collect",
                    headers={"X-API-Key": valid_api_key},
                    json={"sources": ["invalid_source"]}
                )

            assert response.status_code == 400
            assert "No valid sources" in response.json()["detail"]

    def test_collect_default_run_type(self, client, valid_api_key):
        """Test that default run_type is 'manual'."""
        with patch('backend.routes.trigger.get_db') as mock_get_db:
            mock_session = MagicMock()

            def refresh_mock(obj):
                obj.id = 456

            mock_session.refresh = refresh_mock

            def mock_db_generator():
                yield mock_session

            with patch('backend.routes.trigger.get_db', mock_db_generator):
                with patch('backend.routes.trigger._run_collection_job'):
                    response = client.post(
                        "/api/trigger/collect",
                        headers={"X-API-Key": valid_api_key}
                    )

            assert response.status_code == 200
            data = response.json()
            assert data["run_type"] == "manual"


class TestAnalyzeEndpoint:
    """Test /api/trigger/analyze endpoint."""

    def test_analyze_invalid_time_window_returns_400(self, client, valid_api_key):
        """Test that invalid time_window returns 400."""
        with patch('backend.routes.trigger.get_db') as mock_get_db:
            mock_session = MagicMock()

            def mock_db_generator():
                yield mock_session

            with patch('backend.routes.trigger.get_db', mock_db_generator):
                response = client.post(
                    "/api/trigger/analyze",
                    headers={"X-API-Key": valid_api_key},
                    json={"time_window": "invalid"}
                )

            assert response.status_code == 400
            assert "Invalid time_window" in response.json()["detail"]

    def test_analyze_no_content_returns_status(self, client, valid_api_key):
        """Test that analysis with no content returns appropriate status."""
        with patch('backend.routes.trigger.get_db') as mock_get_db:
            mock_session = MagicMock()

            def mock_db_generator():
                yield mock_session

            # Mock empty content query
            with patch('backend.routes.trigger.get_db', mock_db_generator):
                with patch('backend.routes.trigger._get_content_for_synthesis', return_value=[]):
                    response = client.post(
                        "/api/trigger/analyze",
                        headers={"X-API-Key": valid_api_key},
                        json={"time_window": "24h"}
                    )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "no_content"


class TestStatusEndpoint:
    """Test /api/trigger/status endpoints."""

    def test_status_job_not_found_returns_404(self, client, valid_api_key):
        """Test that non-existent job returns 404."""
        with patch('backend.routes.trigger.get_db') as mock_get_db:
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = None

            def mock_db_generator():
                yield mock_session

            with patch('backend.routes.trigger.get_db', mock_db_generator):
                response = client.get(
                    "/api/trigger/status/99999",
                    headers={"X-API-Key": valid_api_key}
                )

            assert response.status_code == 404

    def test_status_returns_job_info(self, client, valid_api_key):
        """Test that status endpoint returns job information."""
        with patch('backend.routes.trigger.get_db') as mock_get_db:
            mock_session = MagicMock()

            # Create a mock collection run
            mock_run = MagicMock()
            mock_run.id = 123
            mock_run.status = "completed"
            mock_run.run_type = "manual"
            mock_run.started_at = datetime(2024, 1, 1, 12, 0, 0)
            mock_run.completed_at = datetime(2024, 1, 1, 12, 5, 0)
            mock_run.total_items_collected = 10
            mock_run.successful_sources = 3
            mock_run.failed_sources = 0
            mock_run.source_results = '{"youtube": {"status": "success"}}'
            mock_run.errors = '[]'

            mock_session.query.return_value.filter.return_value.first.return_value = mock_run

            def mock_db_generator():
                yield mock_session

            with patch('backend.routes.trigger.get_db', mock_db_generator):
                response = client.get(
                    "/api/trigger/status/123",
                    headers={"X-API-Key": valid_api_key}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == 123
            assert data["status"] == "completed"
            assert data["total_items_collected"] == 10

    def test_latest_status_returns_jobs_list(self, client, valid_api_key):
        """Test that status endpoint returns list of recent jobs."""
        with patch('backend.routes.trigger.get_db') as mock_get_db:
            mock_session = MagicMock()

            # Create mock collection runs
            mock_runs = [
                MagicMock(
                    id=1,
                    status="completed",
                    run_type="manual",
                    started_at=datetime(2024, 1, 1, 12, 0, 0),
                    completed_at=datetime(2024, 1, 1, 12, 5, 0),
                    total_items_collected=5,
                    successful_sources=2,
                    failed_sources=0
                ),
                MagicMock(
                    id=2,
                    status="running",
                    run_type="scheduled_6am",
                    started_at=datetime(2024, 1, 2, 11, 0, 0),
                    completed_at=None,
                    total_items_collected=0,
                    successful_sources=0,
                    failed_sources=0
                )
            ]

            mock_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = mock_runs

            def mock_db_generator():
                yield mock_session

            with patch('backend.routes.trigger.get_db', mock_db_generator):
                response = client.get(
                    "/api/trigger/status",
                    headers={"X-API-Key": valid_api_key}
                )

            assert response.status_code == 200
            data = response.json()
            assert "jobs" in data
            assert len(data["jobs"]) == 2


class TestMigrationScript:
    """Test migration script functionality."""

    def test_migration_script_exists(self):
        """Test that migration script exists."""
        from pathlib import Path
        script_path = Path(__file__).parent.parent / "scripts" / "run_migrations.py"
        assert script_path.exists(), "Migration script should exist"

    def test_migration_script_has_auto_flag(self):
        """Test that migration script supports --auto flag."""
        from pathlib import Path
        script_path = Path(__file__).parent.parent / "scripts" / "run_migrations.py"

        content = script_path.read_text()
        assert "--auto" in content, "Migration script should support --auto flag"
        assert "auto_mode" in content, "Migration script should use auto_mode"


class TestRailwayConfig:
    """Test Railway configuration."""

    def test_railway_json_has_nix_packages(self):
        """Test that railway.json includes nixPackages."""
        import json
        from pathlib import Path

        config_path = Path(__file__).parent.parent / "railway.json"
        assert config_path.exists(), "railway.json should exist"

        config = json.loads(config_path.read_text())

        assert "build" in config
        assert "nixPackages" in config["build"]
        assert "ffmpeg" in config["build"]["nixPackages"]
        assert "chromium" in config["build"]["nixPackages"]

    def test_railway_json_runs_migrations(self):
        """Test that railway.json start command runs migrations."""
        import json
        from pathlib import Path

        config_path = Path(__file__).parent.parent / "railway.json"
        config = json.loads(config_path.read_text())

        assert "deploy" in config
        assert "startCommand" in config["deploy"]

        start_cmd = config["deploy"]["startCommand"]
        assert "run_migrations.py" in start_cmd
        assert "--auto" in start_cmd
