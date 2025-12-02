"""
Tests for ConfluenceScorerAgent.

Uses mocked Claude responses to test parsing logic without API calls.
PRD-017: Basic agent tests with mocked Claude responses.
"""

import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


# Sample Claude response for testing
MOCK_CLAUDE_RESPONSE = {
    "pillar_scores": {
        "macro": 2,
        "fundamentals": 1,
        "valuation": 1,
        "positioning": 2,
        "policy": 1,
        "price_action": 1,
        "options_vol": 0
    },
    "reasoning": {
        "macro": "Strong growth data and clear regime shift",
        "fundamentals": "Moderate earnings support",
        "valuation": "Fair value relative to history",
        "positioning": "Clear positioning imbalance",
        "policy": "Supportive fiscal stance",
        "price_action": "Above key moving averages",
        "options_vol": "Insufficient volatility data"
    },
    "core_total": 7,
    "total_score": 8,
    "meets_threshold": True,
    "confluence_level": "strong",
    "primary_thesis": "Fed pivot trade with supportive macro backdrop",
    "falsification_criteria": ["CPI > 4%", "Fed hawkish rhetoric", "Credit spreads widen >50bps"],
    "variant_view": "Market pricing 3 cuts, thesis requires 4+",
    "p_and_l_mechanism": "Long 2Y Treasury futures for duration exposure",
    "conviction_tier": "strong"
}


@pytest.fixture
def mock_env():
    """Set up mock environment variables."""
    with patch.dict(os.environ, {'CLAUDE_API_KEY': 'test-key-12345'}):
        yield


@pytest.fixture
def scorer(mock_env):
    """Create scorer with mocked API key."""
    with patch('agents.base_agent.Anthropic'):
        from agents.confluence_scorer import ConfluenceScorerAgent
        agent = ConfluenceScorerAgent()
        return agent


def test_pillar_definitions(scorer):
    """Test that scorer has correct pillar definitions."""
    assert len(scorer.CORE_PILLARS) == 5
    assert len(scorer.HYBRID_PILLARS) == 2
    assert len(scorer.ALL_PILLARS) == 7
    assert "macro" in scorer.CORE_PILLARS
    assert "options_vol" in scorer.HYBRID_PILLARS


def test_scoring_thresholds(scorer):
    """Test scoring threshold constants."""
    assert scorer.STRONG_CONFLUENCE_CORE_MIN == 6
    assert scorer.MEDIUM_CONFLUENCE_CORE_MIN == 4
    assert scorer.HYBRID_REQUIRED_SCORE == 2


def test_score_content_parsing(scorer):
    """Test that scorer correctly parses Claude response."""
    # Note: The scorer recalculates meets_threshold and confluence_level
    # based on its internal logic, so we verify the recalculated values
    with patch.object(scorer, 'call_claude', return_value=MOCK_CLAUDE_RESPONSE):
        result = scorer.analyze({"content": "test content", "source": "42macro"})

    assert result["total_score"] == 8
    assert result["pillar_scores"]["macro"] == 2
    # With pillar_scores having price_action=1 and options_vol=0,
    # neither hybrid is 2, so meets_threshold should be False
    # even though core_total=7 meets the minimum
    assert result["meets_threshold"] == False
    assert result["confluence_level"] == "medium"  # core >= 4 but threshold not met


def test_core_score_calculation(scorer):
    """Test that core score is calculated correctly."""
    with patch.object(scorer, 'call_claude', return_value=MOCK_CLAUDE_RESPONSE):
        result = scorer.analyze({"content": "test content", "source": "discord"})

    # Core pillars: macro(2) + fundamentals(1) + valuation(1) + positioning(2) + policy(1) = 7
    assert result["core_total"] == 7


def test_threshold_boundary_strong(scorer):
    """Test strong threshold (core >= 6 AND hybrid = 2)."""
    strong_response = {
        **MOCK_CLAUDE_RESPONSE,
        "pillar_scores": {
            "macro": 2, "fundamentals": 1, "valuation": 1,
            "positioning": 2, "policy": 1,
            "price_action": 2, "options_vol": 1
        },
        "core_total": 7,
        "meets_threshold": True,
        "confluence_level": "strong"
    }

    with patch.object(scorer, 'call_claude', return_value=strong_response):
        result = scorer.analyze({"content": "test"})
        assert result["confluence_level"] == "strong"
        assert result["meets_threshold"] == True


def test_threshold_boundary_medium(scorer):
    """Test medium threshold (core 4-5 OR hybrid weak)."""
    medium_response = {
        **MOCK_CLAUDE_RESPONSE,
        "pillar_scores": {
            "macro": 1, "fundamentals": 1, "valuation": 1,
            "positioning": 1, "policy": 1,
            "price_action": 1, "options_vol": 0
        },
        "core_total": 5,
        "meets_threshold": False,
        "confluence_level": "medium"
    }

    with patch.object(scorer, 'call_claude', return_value=medium_response):
        result = scorer.analyze({"content": "test"})
        assert result["confluence_level"] == "medium"


def test_threshold_boundary_weak(scorer):
    """Test weak threshold (core < 4)."""
    weak_response = {
        **MOCK_CLAUDE_RESPONSE,
        "pillar_scores": {
            "macro": 0, "fundamentals": 1, "valuation": 1,
            "positioning": 0, "policy": 1,
            "price_action": 0, "options_vol": 0
        },
        "core_total": 3,
        "meets_threshold": False,
        "confluence_level": "weak"
    }

    with patch.object(scorer, 'call_claude', return_value=weak_response):
        result = scorer.analyze({"content": "test"})
        assert result["confluence_level"] == "weak"


def test_falsification_criteria_present(scorer):
    """Test that falsification criteria are returned."""
    with patch.object(scorer, 'call_claude', return_value=MOCK_CLAUDE_RESPONSE):
        result = scorer.analyze({"content": "test"})

    assert "falsification_criteria" in result
    assert len(result["falsification_criteria"]) > 0
    assert "CPI > 4%" in result["falsification_criteria"]


def test_conviction_tier_mapping(scorer):
    """Test conviction tier is present in output."""
    with patch.object(scorer, 'call_claude', return_value=MOCK_CLAUDE_RESPONSE):
        result = scorer.analyze({"content": "test"})

    assert "conviction_tier" in result
    assert result["conviction_tier"] in ["strong", "medium", "weak"]


def test_primary_thesis_present(scorer):
    """Test that primary thesis is extracted."""
    with patch.object(scorer, 'call_claude', return_value=MOCK_CLAUDE_RESPONSE):
        result = scorer.analyze({"content": "test"})

    assert "primary_thesis" in result
    assert len(result["primary_thesis"]) > 0
