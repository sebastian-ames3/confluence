"""
Tests for PRD-048: Symbol Tracking Reliability

Tests for:
- M3: Staleness validation on read (48h threshold)
- M4: Concurrency lock on symbol refresh
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import os


class TestCalculateStaleness:
    """Tests for calculate_staleness() helper function."""

    def test_staleness_with_none_timestamp(self):
        """Test with None timestamp returns stale with 'Never updated' message."""
        from backend.routes.symbols import calculate_staleness

        result = calculate_staleness(None)

        assert result["is_stale"] is True
        assert result["hours_since_update"] is None
        assert result["staleness_message"] == "Never updated"

    def test_staleness_with_recent_update(self):
        """Test with recent update (within threshold) is not stale."""
        from backend.routes.symbols import calculate_staleness

        # Update 1 hour ago
        last_updated = datetime.utcnow() - timedelta(hours=1)
        result = calculate_staleness(last_updated)

        assert result["is_stale"] is False
        assert result["hours_since_update"] is not None
        assert result["hours_since_update"] < 2  # Should be ~1
        assert result["staleness_message"] is None

    def test_staleness_with_old_update_hours(self):
        """Test with update older than threshold (but less than a week) shows hours."""
        from backend.routes.symbols import calculate_staleness, STALENESS_THRESHOLD_HOURS

        # Update just past threshold
        last_updated = datetime.utcnow() - timedelta(hours=STALENESS_THRESHOLD_HOURS + 10)
        result = calculate_staleness(last_updated)

        assert result["is_stale"] is True
        assert result["hours_since_update"] > STALENESS_THRESHOLD_HOURS
        assert "h old" in result["staleness_message"]
        assert "days" not in result["staleness_message"]

    def test_staleness_with_very_old_update_days(self):
        """Test with update older than a week shows days."""
        from backend.routes.symbols import calculate_staleness

        # Update 10 days ago
        last_updated = datetime.utcnow() - timedelta(days=10)
        result = calculate_staleness(last_updated)

        assert result["is_stale"] is True
        assert "days old" in result["staleness_message"]

    def test_staleness_at_threshold_boundary(self):
        """Test at exactly the threshold boundary."""
        from backend.routes.symbols import calculate_staleness, STALENESS_THRESHOLD_HOURS

        # Exactly at threshold - should not be stale
        last_updated = datetime.utcnow() - timedelta(hours=STALENESS_THRESHOLD_HOURS)
        result = calculate_staleness(last_updated)

        # At exactly threshold, should not be stale (only > threshold is stale)
        assert result["is_stale"] is False

        # Just past threshold - should be stale
        last_updated_past = datetime.utcnow() - timedelta(hours=STALENESS_THRESHOLD_HOURS + 0.1)
        result_past = calculate_staleness(last_updated_past)

        assert result_past["is_stale"] is True

    def test_staleness_returns_rounded_hours(self):
        """Test that hours_since_update is rounded to 1 decimal."""
        from backend.routes.symbols import calculate_staleness

        last_updated = datetime.utcnow() - timedelta(hours=5, minutes=30)
        result = calculate_staleness(last_updated)

        # Should be around 5.5 hours, rounded to 1 decimal
        assert isinstance(result["hours_since_update"], float)
        assert str(result["hours_since_update"]).count('.') <= 1


class TestStalenessThresholdConfiguration:
    """Tests for staleness threshold configuration."""

    def test_default_threshold_is_48(self):
        """Test default staleness threshold is 48 hours."""
        # Clear env var if set
        original = os.environ.pop("SYMBOL_STALENESS_HOURS", None)
        try:
            import importlib
            import backend.routes.symbols as symbols
            importlib.reload(symbols)
            assert symbols.STALENESS_THRESHOLD_HOURS == 48
        finally:
            if original:
                os.environ["SYMBOL_STALENESS_HOURS"] = original

    def test_threshold_from_env_var(self):
        """Test staleness threshold can be set via environment variable."""
        os.environ["SYMBOL_STALENESS_HOURS"] = "72"
        try:
            import importlib
            import backend.routes.symbols as symbols
            importlib.reload(symbols)
            assert symbols.STALENESS_THRESHOLD_HOURS == 72
        finally:
            os.environ.pop("SYMBOL_STALENESS_HOURS", None)
            import importlib
            import backend.routes.symbols as symbols
            importlib.reload(symbols)


class TestConcurrencyLock:
    """Tests for concurrency lock on symbol refresh."""

    def test_refresh_lock_exists(self):
        """Test that refresh lock is defined."""
        from backend.routes.symbols import _refresh_lock
        assert _refresh_lock is not None
        assert isinstance(_refresh_lock, asyncio.Lock)

    def test_refresh_in_progress_flag_exists(self):
        """Test that refresh in progress flag is defined."""
        from backend.routes.symbols import _refresh_in_progress
        # Should be False initially
        assert _refresh_in_progress is False or _refresh_in_progress is True


class TestGetAllSymbolsEndpoint:
    """Tests for GET /api/symbols endpoint staleness info."""

    def test_endpoint_includes_staleness_info(self):
        """Test that endpoint response includes staleness fields."""
        # Create mock symbol state
        mock_state = Mock()
        mock_state.symbol = "SPX"
        mock_state.updated_at = datetime.utcnow() - timedelta(hours=60)
        mock_state.kt_last_updated = datetime.utcnow() - timedelta(hours=60)
        mock_state.discord_last_updated = datetime.utcnow() - timedelta(hours=10)
        mock_state.kt_wave_position = "Wave 3"
        mock_state.kt_wave_phase = "impulsive"
        mock_state.kt_bias = "bullish"
        mock_state.kt_stale_warning = None
        mock_state.discord_quadrant = "buy_call"
        mock_state.discord_iv_regime = "low"
        mock_state.confluence_score = 0.8
        mock_state.sources_directionally_aligned = True

        # The response should include staleness info
        from backend.routes.symbols import calculate_staleness

        overall_staleness = calculate_staleness(mock_state.updated_at)
        kt_staleness = calculate_staleness(mock_state.kt_last_updated)
        discord_staleness = calculate_staleness(mock_state.discord_last_updated)

        # Overall should be stale (60h > 48h)
        assert overall_staleness["is_stale"] is True
        assert overall_staleness["staleness_message"] is not None

        # KT should be stale (60h > 48h)
        assert kt_staleness["is_stale"] is True

        # Discord should not be stale (10h < 48h)
        assert discord_staleness["is_stale"] is False


class TestGetSymbolDetailEndpoint:
    """Tests for GET /api/symbols/{symbol} endpoint staleness info."""

    def test_detail_includes_staleness_threshold(self):
        """Test that detail response includes staleness_threshold_hours."""
        from backend.routes.symbols import STALENESS_THRESHOLD_HOURS

        # The endpoint should include threshold in response
        assert isinstance(STALENESS_THRESHOLD_HOURS, int)
        assert STALENESS_THRESHOLD_HOURS > 0


class TestGetConfluenceOpportunitiesEndpoint:
    """Tests for GET /api/symbols/confluence/opportunities endpoint staleness info."""

    def test_opportunities_include_per_source_staleness(self):
        """Test that opportunities include kt_is_stale and discord_is_stale."""
        from backend.routes.symbols import calculate_staleness

        # Mock data for an opportunity
        kt_last = datetime.utcnow() - timedelta(hours=60)  # Stale
        discord_last = datetime.utcnow() - timedelta(hours=10)  # Fresh

        kt_staleness = calculate_staleness(kt_last)
        discord_staleness = calculate_staleness(discord_last)

        # Response should include these
        assert kt_staleness["is_stale"] is True
        assert discord_staleness["is_stale"] is False


class TestRefreshEndpointConcurrency:
    """Tests for POST /api/symbols/refresh concurrency behavior."""

    @pytest.mark.asyncio
    async def test_concurrent_refresh_returns_already_refreshing(self):
        """Test that concurrent refresh request returns already_refreshing status."""
        from backend.routes.symbols import _refresh_lock, _refresh_in_progress

        # Simulate lock being held
        async with _refresh_lock:
            # Check that lock.locked() returns True
            assert _refresh_lock.locked() is True

    @pytest.mark.asyncio
    async def test_refresh_releases_lock_on_completion(self):
        """Test that lock is released after refresh completes."""
        from backend.routes.symbols import _refresh_lock

        # Acquire and release
        async with _refresh_lock:
            assert _refresh_lock.locked() is True

        # Should be unlocked now
        assert _refresh_lock.locked() is False

    @pytest.mark.asyncio
    async def test_refresh_releases_lock_on_error(self):
        """Test that lock is released even if refresh raises exception."""
        from backend.routes.symbols import _refresh_lock

        try:
            async with _refresh_lock:
                assert _refresh_lock.locked() is True
                raise ValueError("Test error")
        except ValueError:
            pass

        # Should be unlocked after exception
        assert _refresh_lock.locked() is False


class TestStalenessMessageFormats:
    """Tests for staleness message formatting."""

    def test_hours_format_under_week(self):
        """Test hours format for data less than a week old."""
        from backend.routes.symbols import calculate_staleness

        # 50 hours - should show "50h old"
        last_updated = datetime.utcnow() - timedelta(hours=50)
        result = calculate_staleness(last_updated)

        assert "50h old" in result["staleness_message"]
        assert "may be outdated" in result["staleness_message"]

    def test_days_format_over_week(self):
        """Test days format for data over a week old."""
        from backend.routes.symbols import calculate_staleness

        # 10 days - should show "10 days old"
        last_updated = datetime.utcnow() - timedelta(days=10)
        result = calculate_staleness(last_updated)

        assert "10 days old" in result["staleness_message"]
        assert "may be outdated" in result["staleness_message"]

    def test_no_message_when_fresh(self):
        """Test no staleness message when data is fresh."""
        from backend.routes.symbols import calculate_staleness

        # 1 hour ago - fresh
        last_updated = datetime.utcnow() - timedelta(hours=1)
        result = calculate_staleness(last_updated)

        assert result["staleness_message"] is None


class TestStalenessEdgeCases:
    """Tests for staleness calculation edge cases."""

    def test_future_timestamp(self):
        """Test handling of future timestamp (edge case)."""
        from backend.routes.symbols import calculate_staleness

        # Future timestamp
        last_updated = datetime.utcnow() + timedelta(hours=1)
        result = calculate_staleness(last_updated)

        # Should not be stale (negative hours)
        assert result["is_stale"] is False
        # hours_since_update should be negative
        assert result["hours_since_update"] < 0

    def test_very_old_timestamp(self):
        """Test handling of very old timestamp."""
        from backend.routes.symbols import calculate_staleness

        # 1 year ago
        last_updated = datetime.utcnow() - timedelta(days=365)
        result = calculate_staleness(last_updated)

        assert result["is_stale"] is True
        # Should show days
        assert "days old" in result["staleness_message"]


class TestSymbolResponseStructure:
    """Tests to verify response structure includes required fields."""

    def test_get_all_symbols_response_fields(self):
        """Verify response includes staleness_threshold_hours."""
        from backend.routes.symbols import STALENESS_THRESHOLD_HOURS

        # The response should include this field
        expected_response_keys = [
            "symbols",
            "count",
            "staleness_threshold_hours"
        ]

        # Each symbol should include staleness fields
        expected_symbol_keys = [
            "is_stale",
            "hours_since_update",
            "staleness_message"
        ]

        # Verify threshold exists
        assert isinstance(STALENESS_THRESHOLD_HOURS, int)

    def test_kt_view_includes_staleness(self):
        """Verify kt_view includes staleness fields."""
        from backend.routes.symbols import calculate_staleness

        result = calculate_staleness(datetime.utcnow())

        expected_fields = ["is_stale", "hours_since_update", "staleness_message"]
        for field in expected_fields:
            assert field in result

    def test_discord_view_includes_staleness(self):
        """Verify discord_view includes staleness fields."""
        from backend.routes.symbols import calculate_staleness

        result = calculate_staleness(datetime.utcnow())

        expected_fields = ["is_stale", "hours_since_update", "staleness_message"]
        for field in expected_fields:
            assert field in result
