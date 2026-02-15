"""
Tests for Usage Limiter
"""
import pytest
from datetime import date
from backend.utils.usage_limiter import UsageLimiter, get_usage_limiter


class TestUsageLimiter:
    """Test suite for UsageLimiter cost protection."""

    def test_limiter_initialization(self):
        """Test that limiter initializes correctly."""
        limiter = UsageLimiter()
        assert limiter is not None
        assert limiter.MAX_VISION_DAILY == 20
        assert limiter.MAX_TRANSCRIPT_DAILY == 10
        assert limiter.MAX_TEXT_DAILY == 150

    def test_cost_constants(self):
        """Test that cost constants are reasonable."""
        limiter = UsageLimiter()

        # Vision should be most expensive (image tokens)
        assert limiter.COST_PER_VISION == 0.035

        # Transcripts are cheap (YouTube API is free)
        assert limiter.COST_PER_TRANSCRIPT == 0.02

        # Text should be cheap
        assert limiter.COST_PER_TEXT == 0.025

    def test_get_today_usage_empty(self):
        """Test getting usage for today when no usage exists."""
        limiter = UsageLimiter()
        usage = limiter.get_today_usage()

        assert usage["vision_analyses"] >= 0
        assert usage["transcript_analyses"] >= 0
        assert usage["text_analyses"] >= 0
        assert usage["estimated_cost_usd"] >= 0.0

    def test_can_use_vision(self):
        """Test vision API usage check."""
        limiter = UsageLimiter()
        can_use, reason = limiter.can_use_vision(count=1)

        # Should be a boolean and a string
        assert isinstance(can_use, bool)
        assert isinstance(reason, str)

    def test_can_use_transcript(self):
        """Test transcript API usage check."""
        limiter = UsageLimiter()
        can_use, reason = limiter.can_use_transcript(count=1)

        assert isinstance(can_use, bool)
        assert isinstance(reason, str)

    def test_can_use_text(self):
        """Test text API usage check."""
        limiter = UsageLimiter()
        can_use, reason = limiter.can_use_text(count=1)

        assert isinstance(can_use, bool)
        assert isinstance(reason, str)

    def test_budget_status(self):
        """Test getting comprehensive budget status."""
        limiter = UsageLimiter()
        status = limiter.get_budget_status()

        # Check structure
        assert "date" in status
        assert "usage" in status
        assert "limits" in status
        assert "usage_percent" in status
        assert "budget" in status
        assert "warnings" in status

        # Check date format
        assert status["date"] == date.today().isoformat()

        # Check limits
        assert status["limits"]["vision"] == 20
        assert status["limits"]["transcript"] == 10
        assert status["limits"]["text"] == 150

    def test_singleton_instance(self):
        """Test that get_usage_limiter returns singleton."""
        limiter1 = get_usage_limiter()
        limiter2 = get_usage_limiter()

        # Should be the same instance
        assert limiter1 is limiter2


class TestUsageLimiterCostCalculations:
    """Test cost calculation accuracy."""

    def test_daily_budget_calculation(self):
        """Test that daily budget is calculated correctly."""
        limiter = UsageLimiter()

        # Calculate expected max daily budget
        expected_max = (
            limiter.MAX_VISION_DAILY * limiter.COST_PER_VISION +
            limiter.MAX_TRANSCRIPT_DAILY * limiter.COST_PER_TRANSCRIPT +
            limiter.MAX_TEXT_DAILY * limiter.COST_PER_TEXT
        )

        # Should be approximately $4.65/day
        assert 4.0 < expected_max < 5.0

    def test_monthly_budget_projection(self):
        """Test that monthly projection is reasonable."""
        limiter = UsageLimiter()
        status = limiter.get_budget_status()

        monthly_max = status["budget"]["max_monthly"]

        # Should be approximately $243/month (includes synthesis + evaluation costs)
        assert 220 < monthly_max < 270
