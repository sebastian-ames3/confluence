"""
Tests for Trigger API endpoints

Part of PRD-014: Deployment & Infrastructure Fixes
"""
import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestMigrationScript:
    """Test migration script functionality."""

    def test_migration_script_exists(self):
        """Test that migration script exists."""
        script_path = Path(__file__).parent.parent / "scripts" / "run_migrations.py"
        assert script_path.exists(), "Migration script should exist"

    def test_migration_script_has_auto_flag(self):
        """Test that migration script supports --auto flag."""
        script_path = Path(__file__).parent.parent / "scripts" / "run_migrations.py"

        content = script_path.read_text()
        assert "--auto" in content, "Migration script should support --auto flag"
        assert "auto_mode" in content, "Migration script should use auto_mode"

    def test_migration_script_syntax(self):
        """Test that migration script has valid Python syntax."""
        script_path = Path(__file__).parent.parent / "scripts" / "run_migrations.py"
        content = script_path.read_text()
        # This will raise SyntaxError if invalid
        compile(content, str(script_path), 'exec')


class TestRailwayConfig:
    """Test Railway configuration."""

    def test_railway_json_exists(self):
        """Test that railway.json exists."""
        config_path = Path(__file__).parent.parent / "railway.json"
        assert config_path.exists(), "railway.json should exist"

    def test_railway_json_uses_dockerfile(self):
        """Test that railway.json uses Dockerfile builder."""
        config_path = Path(__file__).parent.parent / "railway.json"
        config = json.loads(config_path.read_text())

        assert "build" in config
        assert config["build"]["builder"] == "DOCKERFILE"
        assert "dockerfilePath" in config["build"]

    def test_dockerfile_runs_migrations(self):
        """Test that Dockerfile CMD runs migrations."""
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        assert dockerfile_path.exists(), "Dockerfile should exist"

        content = dockerfile_path.read_text()
        assert "run_migrations.py" in content
        assert "--auto" in content

    def test_railway_json_has_healthcheck(self):
        """Test that railway.json has healthcheck configured."""
        config_path = Path(__file__).parent.parent / "railway.json"
        config = json.loads(config_path.read_text())

        assert "deploy" in config
        assert "healthcheckPath" in config["deploy"]
        assert config["deploy"]["healthcheckPath"] == "/health"


class TestEnvExample:
    """Test environment example configuration."""

    def test_env_example_has_trigger_api_key(self):
        """Test that .env.example includes TRIGGER_API_KEY."""
        env_path = Path(__file__).parent.parent / ".env.example"
        assert env_path.exists(), ".env.example should exist"

        content = env_path.read_text()
        assert "TRIGGER_API_KEY" in content, ".env.example should include TRIGGER_API_KEY"


class TestGitHubWorkflow:
    """Test GitHub Actions workflow configuration."""

    def test_workflow_exists(self):
        """Test that scheduled collection workflow exists."""
        workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "scheduled-collection.yml"
        assert workflow_path.exists(), "scheduled-collection.yml should exist"

    def test_workflow_has_schedule(self):
        """Test that workflow has schedule triggers."""
        workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "scheduled-collection.yml"
        content = workflow_path.read_text()

        assert "schedule:" in content, "Workflow should have schedule trigger"
        assert "cron:" in content, "Workflow should have cron expression"
        # 6am EST = 11:00 UTC
        assert "0 11" in content, "Workflow should run at 11:00 UTC (6am EST)"
        # 6pm EST = 23:00 UTC
        assert "0 23" in content, "Workflow should run at 23:00 UTC (6pm EST)"

    def test_workflow_has_manual_trigger(self):
        """Test that workflow supports manual trigger."""
        workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "scheduled-collection.yml"
        content = workflow_path.read_text()

        assert "workflow_dispatch:" in content, "Workflow should support manual trigger"

    def test_workflow_uses_secrets(self):
        """Test that workflow uses required secrets."""
        workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "scheduled-collection.yml"
        content = workflow_path.read_text()

        assert "RAILWAY_API_URL" in content, "Workflow should use RAILWAY_API_URL secret"
        assert "TRIGGER_API_KEY" in content, "Workflow should use TRIGGER_API_KEY secret"


class TestTriggerRouteModule:
    """Test trigger route module structure."""

    def test_trigger_route_exists(self):
        """Test that trigger route module exists."""
        route_path = Path(__file__).parent.parent / "backend" / "routes" / "trigger.py"
        assert route_path.exists(), "trigger.py should exist"

    def test_trigger_route_syntax(self):
        """Test that trigger route has valid Python syntax."""
        route_path = Path(__file__).parent.parent / "backend" / "routes" / "trigger.py"
        content = route_path.read_text()
        # This will raise SyntaxError if invalid
        compile(content, str(route_path), 'exec')

    def test_trigger_route_has_endpoints(self):
        """Test that trigger route defines expected endpoints."""
        route_path = Path(__file__).parent.parent / "backend" / "routes" / "trigger.py"
        content = route_path.read_text()

        # Check for endpoint decorators
        assert '@router.post("/collect")' in content, "Should have /collect endpoint"
        assert '@router.post("/analyze")' in content, "Should have /analyze endpoint"
        assert '@router.get("/status/{job_id}")' in content, "Should have /status/{job_id} endpoint"
        assert '@router.get("/status")' in content, "Should have /status endpoint"

    def test_trigger_route_has_api_key_auth(self):
        """Test that trigger route implements API key authentication."""
        route_path = Path(__file__).parent.parent / "backend" / "routes" / "trigger.py"
        content = route_path.read_text()

        assert "verify_api_key" in content, "Should have API key verification function"
        assert "X-API-Key" in content, "Should check X-API-Key header"
        assert "TRIGGER_API_KEY" in content, "Should use TRIGGER_API_KEY env var"


class TestAppRegistration:
    """Test that trigger routes are registered in app."""

    def test_app_imports_trigger(self):
        """Test that app.py imports trigger routes."""
        app_path = Path(__file__).parent.parent / "backend" / "app.py"
        content = app_path.read_text()

        assert "trigger" in content, "app.py should import trigger routes"

    def test_app_registers_trigger_router(self):
        """Test that app.py registers trigger router."""
        app_path = Path(__file__).parent.parent / "backend" / "app.py"
        content = app_path.read_text()

        assert "trigger.router" in content, "app.py should register trigger.router"
        assert "/api/trigger" in content, "trigger routes should be mounted at /api/trigger"
