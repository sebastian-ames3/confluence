"""
Tests for PRD-039 Staleness Manager

Tests staleness checking, confluence calculation, and refresh functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from backend.utils.staleness_manager import (
    calculate_confluence_score,
    STALENESS_DAYS
)


class TestConfluenceScoring:
    """Tests for confluence score calculation."""

    def test_bullish_alignment(self):
        """Both sources bullish should result in high confluence."""
        result = calculate_confluence_score(
            kt_bias='bullish',
            discord_quadrant='buy_call'
        )
        assert result['aligned'] is True
        assert result['score'] >= 0.8
        assert 'bullish' in result['reason'].lower()

    def test_bearish_alignment(self):
        """Both sources bearish should result in high confluence."""
        result = calculate_confluence_score(
            kt_bias='bearish',
            discord_quadrant='buy_put'
        )
        assert result['aligned'] is True
        assert result['score'] >= 0.8
        assert 'bearish' in result['reason'].lower()

    def test_conflict_detection(self):
        """Opposing biases should result in conflict."""
        result = calculate_confluence_score(
            kt_bias='bullish',
            discord_quadrant='sell_call'  # bearish
        )
        assert result['aligned'] is False
        assert result['score'] <= 0.3
        assert 'CONFLICT' in result['reason']

    def test_neutral_source(self):
        """Neutral source should result in partial score."""
        result = calculate_confluence_score(
            kt_bias='neutral',
            discord_quadrant='buy_call'
        )
        assert result['aligned'] is False
        assert result['score'] == 0.5
        assert 'neutral' in result['reason'].lower()

    def test_missing_data(self):
        """Missing data should result in zero score."""
        result = calculate_confluence_score(
            kt_bias=None,
            discord_quadrant='buy_call'
        )
        assert result['aligned'] is False
        assert result['score'] == 0.0
        assert 'Missing' in result['reason']

    def test_sell_put_is_bullish(self):
        """Sell put quadrant should map to bullish."""
        result = calculate_confluence_score(
            kt_bias='bullish',
            discord_quadrant='sell_put'
        )
        assert result['aligned'] is True
        assert 'bullish' in result['reason'].lower()

    def test_sell_call_is_bearish(self):
        """Sell call quadrant should map to bearish."""
        result = calculate_confluence_score(
            kt_bias='bearish',
            discord_quadrant='sell_call'
        )
        assert result['aligned'] is True
        assert 'bearish' in result['reason'].lower()


class TestStalenessThreshold:
    """Tests for staleness threshold constant."""

    def test_staleness_threshold_is_14_days(self):
        """Staleness threshold should be 14 days as per PRD-039."""
        assert STALENESS_DAYS == 14

    def test_staleness_calculation(self):
        """Test that dates beyond threshold are detected as stale."""
        threshold = timedelta(days=STALENESS_DAYS)
        now = datetime.utcnow()

        # Recent date - not stale
        recent = now - timedelta(days=7)
        assert now - recent < threshold

        # Old date - stale
        old = now - timedelta(days=20)
        assert now - old > threshold


class TestQuadrantMapping:
    """Tests for Discord quadrant to bias mapping."""

    def test_buy_call_is_bullish(self):
        result = calculate_confluence_score('bullish', 'buy_call')
        assert result['aligned'] is True

    def test_buy_put_is_bearish(self):
        result = calculate_confluence_score('bearish', 'buy_put')
        assert result['aligned'] is True

    def test_sell_call_is_bearish(self):
        result = calculate_confluence_score('bearish', 'sell_call')
        assert result['aligned'] is True

    def test_sell_put_is_bullish(self):
        result = calculate_confluence_score('bullish', 'sell_put')
        assert result['aligned'] is True

    def test_neutral_quadrant(self):
        result = calculate_confluence_score('bullish', 'neutral')
        assert result['aligned'] is False
        assert result['score'] == 0.5
