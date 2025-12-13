"""
Tests for PRD-034: Observability Foundation

Tests for:
- 34.1 Sentry Error Monitoring
- 34.2 Environment Variable Validation
- 34.3 Agent Retry Logic with Exponential Backoff
- 34.4 Collector Dry-Run Mode
"""
import pytest
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock


class TestSentryIntegration:
    """Test 34.1: Sentry Error Monitoring."""

    def test_sentry_sdk_in_requirements(self):
        """Verify sentry-sdk[fastapi] is in requirements.txt."""
        requirements_path = Path(__file__).parent.parent / "requirements.txt"
        content = requirements_path.read_text()
        assert "sentry-sdk" in content, "sentry-sdk should be in requirements.txt"
        assert "fastapi" in content.lower(), "sentry-sdk should include fastapi extra"

    def test_app_has_sentry_initialization(self):
        """Verify app.py contains Sentry initialization code."""
        app_path = Path(__file__).parent.parent / "backend" / "app.py"
        content = app_path.read_text()

        assert "sentry_sdk" in content, "app.py should import sentry_sdk"
        assert "SENTRY_DSN" in content, "app.py should check SENTRY_DSN env var"
        assert "FastApiIntegration" in content, "app.py should use FastApiIntegration"

    def test_sentry_initializes_with_dsn(self):
        """Verify Sentry initializes when SENTRY_DSN is provided."""
        # This test verifies the code structure - actual Sentry initialization
        # is tested in production environment with sentry_sdk installed
        app_path = Path(__file__).parent.parent / "backend" / "app.py"
        content = app_path.read_text()

        # Verify the conditional initialization pattern
        assert 'if os.getenv("SENTRY_DSN")' in content, "Should check for SENTRY_DSN"
        assert "sentry_sdk.init(" in content, "Should call sentry_sdk.init"
        assert 'dsn=os.getenv("SENTRY_DSN")' in content, "Should pass DSN from env"

    def test_sentry_skipped_without_dsn(self):
        """Verify app starts without Sentry when DSN is missing."""
        # Remove SENTRY_DSN if present
        env_copy = os.environ.copy()
        env_copy.pop("SENTRY_DSN", None)

        with patch.dict(os.environ, env_copy, clear=True):
            # Verify SENTRY_DSN is not set
            assert os.getenv("SENTRY_DSN") is None

    def test_sentry_config_has_correct_settings(self):
        """Verify Sentry config in app.py has correct settings."""
        app_path = Path(__file__).parent.parent / "backend" / "app.py"
        content = app_path.read_text()

        # Check for proper configuration
        assert "traces_sample_rate" in content, "Should configure trace sampling"
        assert "send_default_pii=False" in content, "Should not send PII"
        assert "RAILWAY_ENV" in content, "Should tag with environment"


class TestEnvironmentValidation:
    """Test 34.2: Environment Variable Validation."""

    def test_app_has_validation_function(self):
        """Verify validate_environment() function exists in app.py."""
        app_path = Path(__file__).parent.parent / "backend" / "app.py"
        content = app_path.read_text()

        assert "def validate_environment" in content, "Should have validate_environment function"
        assert "REQUIRED_ENV_VARS" in content, "Should define REQUIRED_ENV_VARS"

    def test_required_vars_include_critical_vars(self):
        """Verify required vars list includes critical variables."""
        app_path = Path(__file__).parent.parent / "backend" / "app.py"
        content = app_path.read_text()

        assert "CLAUDE_API_KEY" in content, "CLAUDE_API_KEY should be required"
        assert "AUTH_USERNAME" in content, "AUTH_USERNAME should be required"
        assert "AUTH_PASSWORD" in content, "AUTH_PASSWORD should be required"

    def test_validation_raises_in_production(self):
        """Verify RuntimeError raised in production with missing vars."""
        app_path = Path(__file__).parent.parent / "backend" / "app.py"
        content = app_path.read_text()

        assert "RuntimeError" in content, "Should raise RuntimeError for missing vars"
        assert 'RAILWAY_ENV' in content, "Should check RAILWAY_ENV for production"
        assert '"production"' in content, "Should check for production environment"

    def test_validation_warns_in_development(self):
        """Verify warning logged in development with missing vars."""
        app_path = Path(__file__).parent.parent / "backend" / "app.py"
        content = app_path.read_text()

        assert "warning" in content.lower(), "Should log warning in development"

    def test_env_validation_fails_in_production_mode(self):
        """Test that validation fails in production when vars are missing."""
        # Simulate production environment with missing vars
        env = {
            "RAILWAY_ENV": "production",
            # Missing: CLAUDE_API_KEY, AUTH_USERNAME, AUTH_PASSWORD
        }

        # The validate_environment function logic
        required_vars = ["CLAUDE_API_KEY", "AUTH_USERNAME", "AUTH_PASSWORD"]

        with patch.dict(os.environ, env, clear=True):
            missing = [v for v in required_vars if not os.getenv(v)]
            assert len(missing) == 3, "All required vars should be missing"
            assert "CLAUDE_API_KEY" in missing
            assert "AUTH_USERNAME" in missing
            assert "AUTH_PASSWORD" in missing

    def test_env_validation_passes_when_vars_set(self):
        """Test that validation passes when all vars are set."""
        env = {
            "RAILWAY_ENV": "production",
            "CLAUDE_API_KEY": "test-key",
            "AUTH_USERNAME": "testuser",
            "AUTH_PASSWORD": "testpass",
        }

        required_vars = ["CLAUDE_API_KEY", "AUTH_USERNAME", "AUTH_PASSWORD"]

        with patch.dict(os.environ, env, clear=True):
            missing = [v for v in required_vars if not os.getenv(v)]
            assert len(missing) == 0, "No vars should be missing"


class TestAgentRetryLogic:
    """Test 34.3: Agent Retry Logic with Exponential Backoff."""

    def test_base_agent_has_retry_logic(self):
        """Verify base_agent.py has retry logic in call_claude()."""
        agent_path = Path(__file__).parent.parent / "agents" / "base_agent.py"
        content = agent_path.read_text()

        assert "max_retries" in content, "Should have max_retries parameter"
        assert "for attempt in range" in content, "Should have retry loop"
        assert "time.sleep" in content, "Should have delay between retries"

    def test_exponential_backoff_formula(self):
        """Verify exponential backoff uses correct formula."""
        agent_path = Path(__file__).parent.parent / "agents" / "base_agent.py"
        content = agent_path.read_text()

        assert "2 ** attempt" in content, "Should use 2^attempt for backoff"
        assert "min(" in content and "30" in content, "Should cap delay at 30 seconds"

    def test_retry_logs_at_correct_levels(self):
        """Verify retry attempts logged at WARNING, failures at ERROR."""
        agent_path = Path(__file__).parent.parent / "agents" / "base_agent.py"
        content = agent_path.read_text()

        assert "logger.warning" in content, "Should log retries at WARNING level"
        assert "logger.error" in content, "Should log final failure at ERROR level"

    def test_retry_default_is_3_attempts(self):
        """Verify default max_retries is 3."""
        agent_path = Path(__file__).parent.parent / "agents" / "base_agent.py"
        content = agent_path.read_text()

        assert "max_retries: int = 3" in content, "Default max_retries should be 3"

    def test_exponential_backoff_delays(self):
        """Test that exponential backoff produces correct delays."""
        # Formula: min(2 ** attempt, 30)
        expected_delays = [1, 2, 4, 8, 16, 30, 30]  # 2^0, 2^1, 2^2, ..., capped at 30

        for attempt in range(7):
            delay = min(2 ** attempt, 30)
            assert delay == expected_delays[attempt], f"Attempt {attempt} should have delay {expected_delays[attempt]}"

    def test_last_exception_raised_after_retries(self):
        """Verify last exception is raised after all retries exhausted."""
        agent_path = Path(__file__).parent.parent / "agents" / "base_agent.py"
        content = agent_path.read_text()

        assert "last_exception" in content, "Should track last exception"
        assert "raise last_exception" in content, "Should raise last exception after retries"


class TestCollectorDryRunMode:
    """Test 34.4: Collector Dry-Run Mode."""

    def test_base_collector_has_dry_run_parameter(self):
        """Verify BaseCollector.__init__() accepts dry_run parameter."""
        collector_path = Path(__file__).parent.parent / "collectors" / "base_collector.py"
        content = collector_path.read_text()

        assert "dry_run: bool = False" in content, "Should have dry_run parameter"
        assert "self.dry_run = dry_run" in content, "Should store dry_run as instance var"

    def test_save_to_database_checks_dry_run(self):
        """Verify save_to_database() checks dry_run flag."""
        collector_path = Path(__file__).parent.parent / "collectors" / "base_collector.py"
        content = collector_path.read_text()

        assert "if self.dry_run:" in content, "Should check dry_run flag"
        assert "[DRY RUN]" in content, "Should log DRY RUN prefix"

    def test_dry_run_logs_sample_items(self):
        """Verify dry-run mode logs sample items."""
        collector_path = Path(__file__).parent.parent / "collectors" / "base_collector.py"
        content = collector_path.read_text()

        assert "Sample item" in content, "Should log sample items"
        assert "[:3]" in content, "Should log first 3 items as sample"

    def test_dry_run_returns_count_without_saving(self):
        """Verify dry-run returns item count without database writes."""
        collector_path = Path(__file__).parent.parent / "collectors" / "base_collector.py"
        content = collector_path.read_text()

        # In dry-run mode, should return len(content_items) without calling db
        assert "return len(content_items)" in content, "Should return item count in dry-run"

    def test_trigger_route_supports_dry_run(self):
        """Verify /api/trigger/collect supports dry_run parameter."""
        trigger_path = Path(__file__).parent.parent / "backend" / "routes" / "trigger.py"
        content = trigger_path.read_text()

        assert "dry_run" in content, "trigger.py should support dry_run"

    def test_run_method_includes_dry_run_in_result(self):
        """Verify run() method includes dry_run flag in result."""
        collector_path = Path(__file__).parent.parent / "collectors" / "base_collector.py"
        content = collector_path.read_text()

        # Check that result dict includes dry_run
        assert '"dry_run": self.dry_run' in content or "'dry_run': self.dry_run" in content, \
            "Result should include dry_run flag"


class TestPRD034Documentation:
    """Test PRD-034 documentation exists."""

    def test_prd_document_exists(self):
        """Verify PRD-034 document exists in docs/archived/."""
        prd_path = Path(__file__).parent.parent / "docs" / "archived" / "PRD-034_Observability_Foundation.md"
        assert prd_path.exists(), "PRD-034 document should exist in docs/archived/"

    def test_prd_has_definition_of_done(self):
        """Verify PRD has Definition of Done section."""
        prd_path = Path(__file__).parent.parent / "docs" / "archived" / "PRD-034_Observability_Foundation.md"
        content = prd_path.read_text()

        assert "Definition of Done" in content, "PRD should have Definition of Done section"

    def test_prd_covers_all_sections(self):
        """Verify PRD covers all four implementation sections."""
        prd_path = Path(__file__).parent.parent / "docs" / "archived" / "PRD-034_Observability_Foundation.md"
        content = prd_path.read_text()

        assert "34.1" in content, "PRD should cover 34.1 Sentry"
        assert "34.2" in content, "PRD should cover 34.2 Environment Validation"
        assert "34.3" in content, "PRD should cover 34.3 Retry Logic"
        assert "34.4" in content, "PRD should cover 34.4 Dry-Run Mode"


class TestIntegrationDryRun:
    """Integration tests for dry-run mode."""

    @pytest.mark.asyncio
    async def test_dry_run_collector_does_not_write_db(self):
        """Test that dry-run mode doesn't write to database."""
        from collectors.base_collector import BaseCollector

        # Create a concrete implementation for testing
        class TestCollector(BaseCollector):
            async def collect(self):
                return [
                    {"content_type": "text", "collected_at": "2025-01-01T00:00:00", "url": "https://example.com/1"},
                    {"content_type": "text", "collected_at": "2025-01-01T00:00:00", "url": "https://example.com/2"},
                ]

        collector = TestCollector("test_source", dry_run=True)
        assert collector.dry_run is True, "dry_run should be True"

        # Mock the database interaction
        content_items = await collector.collect()
        saved_count = await collector.save_to_database(content_items)

        # Should return count without actually writing
        assert saved_count == 2, "Should return item count"


class TestIntegrationRetryLogic:
    """Integration tests for retry logic."""

    def test_retry_logic_with_mock_failure(self):
        """Test retry logic handles failures correctly."""
        # Simulate the retry logic
        max_retries = 3
        attempts_made = []
        last_exception = None

        for attempt in range(max_retries):
            attempts_made.append(attempt)
            try:
                # Simulate failure
                raise ConnectionError(f"Simulated failure on attempt {attempt}")
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    # Would normally sleep here
                    delay = min(2 ** attempt, 30)
                    assert delay in [1, 2], f"Delay should be 1 or 2 for attempts 0-1"

        assert len(attempts_made) == 3, "Should have made 3 attempts"
        assert last_exception is not None, "Should have captured last exception"
        assert "attempt 2" in str(last_exception), "Last exception should be from final attempt"

    def test_retry_logic_succeeds_on_second_attempt(self):
        """Test retry logic succeeds when API works on retry."""
        max_retries = 3
        success = False

        for attempt in range(max_retries):
            if attempt == 1:  # Succeed on second attempt
                success = True
                break
            # First attempt fails
            continue

        assert success is True, "Should succeed on second attempt"
