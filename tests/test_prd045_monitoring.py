"""
Tests for PRD-045: Collection Monitoring & Alerting

Tests for:
- 45.1 Database Models (TranscriptionStatus, SourceHealth, Alert)
- 45.2 Transcription Tracking
- 45.3 Health API Endpoints
- 45.4 Alerting Service
- 45.5 Frontend Health Widget
- 45.7 Heartbeat Expansion
- 45.8 Sync Transcription Mode
"""
import pytest
from pathlib import Path
from datetime import datetime, timedelta


class TestMonitoringModels:
    """Test 45.1: Database models for monitoring."""

    def test_models_file_exists(self):
        """Verify models.py exists."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        assert models_path.exists(), "models.py should exist"

    def test_transcription_status_model_exists(self):
        """Verify TranscriptionStatus model is defined."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        assert "class TranscriptionStatus" in content
        assert '__tablename__ = "transcription_status"' in content

    def test_transcription_status_has_required_columns(self):
        """Verify TranscriptionStatus has all required columns."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        required_columns = [
            "content_id",
            "status",
            "error_message",
            "retry_count",
            "last_attempt_at",
            "completed_at",
            "created_at",
            "updated_at"
        ]

        for col in required_columns:
            assert col in content, f"TranscriptionStatus should have {col} column"

    def test_transcription_status_has_status_constraint(self):
        """Verify TranscriptionStatus has status enum constraint."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        assert "pending" in content
        assert "processing" in content
        assert "completed" in content
        assert "failed" in content
        assert "skipped" in content

    def test_source_health_model_exists(self):
        """Verify SourceHealth model is defined."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        assert "class SourceHealth" in content
        assert '__tablename__ = "source_health"' in content

    def test_source_health_has_required_columns(self):
        """Verify SourceHealth has all required columns."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        required_columns = [
            "source_name",
            "last_collection_at",
            "last_collection_status",
            "last_transcription_at",
            "items_collected_24h",
            "items_transcribed_24h",
            "errors_24h",
            "consecutive_failures",
            "is_stale",
            "updated_at"
        ]

        for col in required_columns:
            assert col in content, f"SourceHealth should have {col} column"

    def test_alert_model_exists(self):
        """Verify Alert model is defined."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        assert "class Alert" in content
        assert '__tablename__ = "alerts"' in content

    def test_alert_has_required_columns(self):
        """Verify Alert has all required columns."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        required_columns = [
            "alert_type",
            "source",
            "severity",
            "message",
            "is_acknowledged",
            "acknowledged_at",
            "acknowledged_by",
            "created_at",
            "expires_at"
        ]

        for col in required_columns:
            assert col in content, f"Alert should have {col} column"

    def test_alert_has_severity_constraint(self):
        """Verify Alert has severity constraint."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        assert "critical" in content
        assert "high" in content
        assert "medium" in content
        assert "low" in content

    def test_alert_has_type_constraint(self):
        """Verify Alert has alert_type constraint."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        assert "collection_failed" in content
        assert "transcription_backlog" in content
        assert "source_stale" in content
        assert "error_spike" in content


class TestTranscriptionTracking:
    """Test 45.2: Transcription tracking in collection."""

    def test_collect_py_exists(self):
        """Verify collect.py exists."""
        collect_path = Path(__file__).parent.parent / "backend" / "routes" / "collect.py"
        assert collect_path.exists(), "collect.py should exist"

    def test_transcribe_with_tracking_function_exists(self):
        """Verify _transcribe_video_with_tracking function exists."""
        collect_path = Path(__file__).parent.parent / "backend" / "routes" / "collect.py"
        content = collect_path.read_text()

        assert "_transcribe_video_with_tracking" in content

    def test_queue_transcription_with_tracking_exists(self):
        """Verify _queue_transcription_with_tracking function exists."""
        collect_path = Path(__file__).parent.parent / "backend" / "routes" / "collect.py"
        content = collect_path.read_text()

        assert "_queue_transcription_with_tracking" in content

    def test_transcription_status_import(self):
        """Verify TranscriptionStatus is imported in collect.py."""
        collect_path = Path(__file__).parent.parent / "backend" / "routes" / "collect.py"
        content = collect_path.read_text()

        assert "TranscriptionStatus" in content

    def test_sync_transcription_mode_config(self):
        """Verify SYNC_TRANSCRIPTION env var config exists."""
        collect_path = Path(__file__).parent.parent / "backend" / "routes" / "collect.py"
        content = collect_path.read_text()

        assert "SYNC_TRANSCRIPTION" in content
        assert 'os.getenv("SYNC_TRANSCRIPTION"' in content


class TestHealthAPI:
    """Test 45.3: Health API endpoints."""

    def test_health_routes_file_exists(self):
        """Verify health.py routes file exists."""
        health_path = Path(__file__).parent.parent / "backend" / "routes" / "health.py"
        assert health_path.exists(), "health.py should exist"

    def test_health_sources_endpoint(self):
        """Verify /health/sources endpoint exists."""
        health_path = Path(__file__).parent.parent / "backend" / "routes" / "health.py"
        content = health_path.read_text()

        assert '@router.get("/sources")' in content
        assert "get_all_source_health" in content

    def test_health_sources_detail_endpoint(self):
        """Verify /health/sources/{source} endpoint exists."""
        health_path = Path(__file__).parent.parent / "backend" / "routes" / "health.py"
        content = health_path.read_text()

        assert '@router.get("/sources/{source_name}")' in content
        assert "get_source_health_detail" in content

    def test_health_transcription_endpoint(self):
        """Verify /health/transcription endpoint exists."""
        health_path = Path(__file__).parent.parent / "backend" / "routes" / "health.py"
        content = health_path.read_text()

        assert '@router.get("/transcription")' in content
        assert "get_transcription_queue_status" in content

    def test_health_alerts_endpoint(self):
        """Verify /health/alerts endpoint exists."""
        health_path = Path(__file__).parent.parent / "backend" / "routes" / "health.py"
        content = health_path.read_text()

        assert '@router.get("/alerts")' in content
        assert "get_active_alerts" in content

    def test_health_alerts_acknowledge_endpoint(self):
        """Verify alert acknowledgment endpoint exists."""
        health_path = Path(__file__).parent.parent / "backend" / "routes" / "health.py"
        content = health_path.read_text()

        assert '@router.post("/alerts/{alert_id}/acknowledge")' in content
        assert "acknowledge_alert" in content

    def test_health_check_alerts_endpoint(self):
        """Verify alert check trigger endpoint exists."""
        health_path = Path(__file__).parent.parent / "backend" / "routes" / "health.py"
        content = health_path.read_text()

        assert '@router.post("/check-alerts")' in content
        assert "trigger_alert_check" in content

    def test_health_router_registered(self):
        """Verify health router is registered in app.py."""
        app_path = Path(__file__).parent.parent / "backend" / "app.py"
        content = app_path.read_text()

        assert "health.router" in content or "health" in content


class TestAlertingService:
    """Test 45.4: Alerting service."""

    def test_services_directory_exists(self):
        """Verify backend/services directory exists."""
        services_path = Path(__file__).parent.parent / "backend" / "services"
        assert services_path.exists(), "backend/services should exist"

    def test_alerting_file_exists(self):
        """Verify alerting.py exists."""
        alerting_path = Path(__file__).parent.parent / "backend" / "services" / "alerting.py"
        assert alerting_path.exists(), "alerting.py should exist"

    def test_check_and_create_alerts_function(self):
        """Verify check_and_create_alerts function exists."""
        alerting_path = Path(__file__).parent.parent / "backend" / "services" / "alerting.py"
        content = alerting_path.read_text()

        assert "async def check_and_create_alerts" in content

    def test_create_alert_if_not_exists_function(self):
        """Verify _create_alert_if_not_exists function exists."""
        alerting_path = Path(__file__).parent.parent / "backend" / "services" / "alerting.py"
        content = alerting_path.read_text()

        assert "_create_alert_if_not_exists" in content

    def test_alert_thresholds_defined(self):
        """Verify alert thresholds are defined."""
        alerting_path = Path(__file__).parent.parent / "backend" / "services" / "alerting.py"
        content = alerting_path.read_text()

        assert "CONSECUTIVE_FAILURE_THRESHOLD" in content
        assert "STALENESS_THRESHOLD_HOURS" in content
        assert "TRANSCRIPTION_BACKLOG_HOURS" in content
        assert "ERROR_SPIKE_THRESHOLD" in content

    def test_monitored_sources_defined(self):
        """Verify monitored sources are defined."""
        alerting_path = Path(__file__).parent.parent / "backend" / "services" / "alerting.py"
        content = alerting_path.read_text()

        assert "MONITORED_SOURCES" in content
        assert "youtube" in content
        assert "discord" in content
        assert "42macro" in content

    def test_video_sources_defined(self):
        """Verify video sources are defined."""
        alerting_path = Path(__file__).parent.parent / "backend" / "services" / "alerting.py"
        content = alerting_path.read_text()

        assert "VIDEO_SOURCES" in content

    def test_record_collection_result_function(self):
        """Verify record_collection_result function exists."""
        alerting_path = Path(__file__).parent.parent / "backend" / "services" / "alerting.py"
        content = alerting_path.read_text()

        assert "async def record_collection_result" in content


class TestFrontendHealthWidget:
    """Test 45.5: Frontend health widget."""

    def test_health_js_exists(self):
        """Verify health.js exists."""
        health_js_path = Path(__file__).parent.parent / "frontend" / "js" / "health.js"
        assert health_js_path.exists(), "health.js should exist"

    def test_health_manager_defined(self):
        """Verify HealthManager is defined in health.js."""
        health_js_path = Path(__file__).parent.parent / "frontend" / "js" / "health.js"
        content = health_js_path.read_text(encoding="utf-8")

        assert "HealthManager" in content
        assert "init()" in content or "init:" in content

    def test_health_widget_methods(self):
        """Verify HealthManager has required methods."""
        health_js_path = Path(__file__).parent.parent / "frontend" / "js" / "health.js"
        content = health_js_path.read_text(encoding="utf-8")

        required_methods = [
            "createHealthWidget",
            "fetchAndDisplay",
            "updateDisplay",
            "renderSourcesList",
            "renderAlertsList",
            "acknowledgeAlert"
        ]

        for method in required_methods:
            assert method in content, f"HealthManager should have {method} method"

    def test_health_css_exists(self):
        """Verify health CSS file exists."""
        health_css_path = Path(__file__).parent.parent / "frontend" / "css" / "components" / "_health.css"
        assert health_css_path.exists(), "_health.css should exist"

    def test_health_css_has_required_classes(self):
        """Verify health CSS has required classes."""
        health_css_path = Path(__file__).parent.parent / "frontend" / "css" / "components" / "_health.css"
        content = health_css_path.read_text(encoding="utf-8")

        required_classes = [
            ".health-widget",
            ".health-indicator",
            ".health-dot",
            ".health-dropdown",
            ".health-source-item",
            ".health-alert-item"
        ]

        for css_class in required_classes:
            assert css_class in content, f"_health.css should have {css_class}"

    def test_health_css_imported(self):
        """Verify health CSS is imported in components.css."""
        components_css_path = Path(__file__).parent.parent / "frontend" / "css" / "components" / "components.css"
        content = components_css_path.read_text(encoding="utf-8")

        assert "_health.css" in content

    def test_health_js_included_in_html(self):
        """Verify health.js is included in index.html."""
        index_path = Path(__file__).parent.parent / "frontend" / "index.html"
        content = index_path.read_text(encoding="utf-8")

        assert "health.js" in content


class TestGitHubActionsIntegration:
    """Test 45.6: GitHub Actions workflow updates."""

    def test_scheduled_collection_workflow_exists(self):
        """Verify scheduled-collection.yml exists."""
        workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "scheduled-collection.yml"
        assert workflow_path.exists(), "scheduled-collection.yml should exist"

    def test_health_check_step_exists(self):
        """Verify health check step exists in workflow."""
        workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "scheduled-collection.yml"
        content = workflow_path.read_text()

        assert "Check Collection Health" in content
        assert "/health/sources" in content

    def test_transcription_status_check_exists(self):
        """Verify transcription status check exists in workflow."""
        workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "scheduled-collection.yml"
        content = workflow_path.read_text()

        assert "Check Transcription Status" in content
        assert "/health/transcription" in content

    def test_alert_check_step_exists(self):
        """Verify alert check step exists in workflow."""
        workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "scheduled-collection.yml"
        content = workflow_path.read_text()

        assert "Run Alert Check" in content
        assert "/health/check-alerts" in content

    def test_health_check_runs_always(self):
        """Verify health check runs even on failure."""
        workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "scheduled-collection.yml"
        content = workflow_path.read_text()

        assert "if: always()" in content


class TestHeartbeatExpansion:
    """Test 45.7: Heartbeat expansion for all sources."""

    def test_heartbeat_thresholds_defined(self):
        """Verify heartbeat thresholds are defined for all sources."""
        heartbeat_path = Path(__file__).parent.parent / "backend" / "routes" / "heartbeat.py"
        content = heartbeat_path.read_text()

        assert "HEARTBEAT_THRESHOLDS" in content
        assert '"discord"' in content
        assert '"42macro"' in content
        assert '"youtube"' in content
        assert '"substack"' in content
        assert '"kt_technical"' in content

    def test_generic_heartbeat_endpoint(self):
        """Verify generic heartbeat endpoint exists."""
        heartbeat_path = Path(__file__).parent.parent / "backend" / "routes" / "heartbeat.py"
        content = heartbeat_path.read_text()

        assert '@router.post("/heartbeat/{service_name}")' in content
        assert "record_service_heartbeat" in content

    def test_all_heartbeat_status_endpoint(self):
        """Verify /heartbeat/all endpoint exists."""
        heartbeat_path = Path(__file__).parent.parent / "backend" / "routes" / "heartbeat.py"
        content = heartbeat_path.read_text()

        assert '@router.get("/heartbeat/all")' in content
        assert "get_all_heartbeat_status" in content


class TestSyncTranscriptionMode:
    """Test 45.8: Synchronous transcription mode."""

    def test_sync_mode_env_var(self):
        """Verify SYNC_TRANSCRIPTION env var is read."""
        collect_path = Path(__file__).parent.parent / "backend" / "routes" / "collect.py"
        content = collect_path.read_text()

        assert 'SYNC_TRANSCRIPTION = os.getenv("SYNC_TRANSCRIPTION"' in content

    def test_sync_mode_conditional_logic(self):
        """Verify sync mode conditional logic exists."""
        collect_path = Path(__file__).parent.parent / "backend" / "routes" / "collect.py"
        content = collect_path.read_text()

        assert "if SYNC_TRANSCRIPTION" in content

    def test_transcription_mode_in_response(self):
        """Verify transcription mode is included in response."""
        collect_path = Path(__file__).parent.parent / "backend" / "routes" / "collect.py"
        content = collect_path.read_text()

        assert "transcription_mode" in content


class TestIntegration:
    """Integration tests for the monitoring system."""

    def test_models_can_be_imported(self):
        """Test that monitoring models can be imported."""
        try:
            from backend.models import TranscriptionStatus, SourceHealth, Alert
            assert TranscriptionStatus is not None
            assert SourceHealth is not None
            assert Alert is not None
        except ImportError as e:
            pytest.fail(f"Failed to import monitoring models: {e}")

    def test_alerting_service_can_be_imported(self):
        """Test that alerting service can be imported."""
        try:
            from backend.services.alerting import check_and_create_alerts, record_collection_result
            assert check_and_create_alerts is not None
            assert record_collection_result is not None
        except ImportError as e:
            pytest.fail(f"Failed to import alerting service: {e}")

    def test_health_routes_can_be_imported(self):
        """Test that health routes can be imported."""
        try:
            from backend.routes.health import router
            assert router is not None
        except ImportError as e:
            pytest.fail(f"Failed to import health routes: {e}")
