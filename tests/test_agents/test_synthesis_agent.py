"""
Tests for SynthesisAgent.

Uses mocked Claude responses to test synthesis logic.
PRD-017: Basic agent tests with mocked Claude responses.
"""

import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


# Sample Claude response for testing
MOCK_SYNTHESIS_RESPONSE = {
    "synthesis": "Markets are showing clear risk-on sentiment with multiple sources highlighting the Fed pivot narrative. 42 Macro's latest research emphasizes improving growth indicators while Options Insight notes increasing call skew in equities. The confluence across macro data, positioning, and technicals suggests a favorable setup for risk assets.",
    "key_themes": ["Fed pivot", "Tech rotation", "Improving growth", "Supportive liquidity"],
    "high_conviction_ideas": [
        {
            "idea": "Long gold on real rate decline",
            "sources": ["42macro", "substack"],
            "confidence": "high",
            "rationale": "Multiple sources cite declining real rates as supportive"
        },
        {
            "idea": "Overweight tech vs value",
            "sources": ["kt_technical", "discord"],
            "confidence": "medium",
            "rationale": "Technical breakout aligns with options positioning"
        }
    ],
    "contradictions": [
        {
            "topic": "Duration positioning",
            "views": ["42macro bullish long end", "discord cautious on rates"],
            "resolution": "Time horizon difference - short-term vol vs medium-term trend"
        }
    ],
    "market_regime": "risk-on",
    "catalysts": ["FOMC meeting Dec 18", "CPI release Dec 11", "Earnings season Jan"],
    "risks": ["Inflation reacceleration", "Geopolitical escalation"]
}


@pytest.fixture
def mock_env():
    """Set up mock environment variables."""
    with patch.dict(os.environ, {'CLAUDE_API_KEY': 'test-key-12345'}):
        yield


@pytest.fixture
def agent(mock_env):
    """Create synthesis agent with mocked API key."""
    with patch('agents.base_agent.Anthropic'):
        from agents.synthesis_agent import SynthesisAgent
        return SynthesisAgent()


def test_source_weights_defined(agent):
    """Test that source weights are properly defined."""
    assert "42macro" in agent.SOURCE_WEIGHTS
    assert "discord" in agent.SOURCE_WEIGHTS
    assert "youtube" in agent.SOURCE_WEIGHTS
    assert "substack" in agent.SOURCE_WEIGHTS
    assert "kt_technical" in agent.SOURCE_WEIGHTS


def test_system_prompt_exists(agent):
    """Test that system prompt is defined."""
    assert hasattr(agent, 'SYSTEM_PROMPT')
    assert len(agent.SYSTEM_PROMPT) > 100
    assert "macro analyst" in agent.SYSTEM_PROMPT.lower()


def test_synthesis_generation(agent):
    """Test synthesis generates expected structure."""
    content_items = [
        {"source": "42macro", "summary": "Bullish on gold", "themes": ["gold", "rates"]},
        {"source": "discord", "summary": "Vol surface bullish", "themes": ["volatility"]}
    ]

    with patch.object(agent, 'call_claude', return_value=MOCK_SYNTHESIS_RESPONSE):
        result = agent.analyze(content_items, time_window="24h")

    assert "synthesis" in result
    assert "key_themes" in result
    assert result["time_window"] == "24h"


def test_empty_content_handling(agent):
    """Test synthesis handles empty content gracefully."""
    result = agent.analyze([], time_window="24h")

    assert result["content_count"] == 0
    assert "synthesis" in result
    # Should indicate no content available
    assert "no content" in result["synthesis"].lower() or result["synthesis"] == ""


def test_high_conviction_ideas_structure(agent):
    """Test high conviction ideas have proper structure."""
    content_items = [{"source": "42macro", "summary": "test"}]

    with patch.object(agent, 'call_claude', return_value=MOCK_SYNTHESIS_RESPONSE):
        result = agent.analyze(content_items, time_window="24h")

    assert "high_conviction_ideas" in result
    if result["high_conviction_ideas"]:
        idea = result["high_conviction_ideas"][0]
        assert "idea" in idea
        assert "sources" in idea
        assert "confidence" in idea


def test_market_regime_classification(agent):
    """Test market regime is classified."""
    content_items = [{"source": "42macro", "summary": "test"}]

    with patch.object(agent, 'call_claude', return_value=MOCK_SYNTHESIS_RESPONSE):
        result = agent.analyze(content_items, time_window="24h")

    assert "market_regime" in result
    assert result["market_regime"] in ["risk-on", "risk-off", "transitioning", "unclear", None]


def test_contradictions_detected(agent):
    """Test contradictions are surfaced."""
    content_items = [
        {"source": "42macro", "summary": "Bullish bonds"},
        {"source": "discord", "summary": "Bearish bonds"}
    ]

    with patch.object(agent, 'call_claude', return_value=MOCK_SYNTHESIS_RESPONSE):
        result = agent.analyze(content_items, time_window="24h")

    assert "contradictions" in result


def test_key_themes_extraction(agent):
    """Test key themes are extracted."""
    content_items = [{"source": "42macro", "summary": "Fed pivot narrative"}]

    with patch.object(agent, 'call_claude', return_value=MOCK_SYNTHESIS_RESPONSE):
        result = agent.analyze(content_items, time_window="24h")

    assert "key_themes" in result
    assert isinstance(result["key_themes"], list)
    assert len(result["key_themes"]) > 0


def test_time_window_options(agent):
    """Test different time windows are accepted."""
    content_items = [{"source": "42macro", "summary": "test"}]

    for time_window in ["24h", "7d", "30d"]:
        with patch.object(agent, 'call_claude', return_value=MOCK_SYNTHESIS_RESPONSE):
            result = agent.analyze(content_items, time_window=time_window)
            assert result["time_window"] == time_window


def test_focus_topic_parameter(agent):
    """Test focus topic parameter is accepted."""
    content_items = [{"source": "42macro", "summary": "Gold analysis"}]

    with patch.object(agent, 'call_claude', return_value=MOCK_SYNTHESIS_RESPONSE):
        result = agent.analyze(content_items, time_window="24h", focus_topic="gold")

    # Should complete without error
    assert "synthesis" in result


def test_catalysts_included(agent):
    """Test catalysts are included in output."""
    content_items = [{"source": "42macro", "summary": "FOMC upcoming"}]

    with patch.object(agent, 'call_claude', return_value=MOCK_SYNTHESIS_RESPONSE):
        result = agent.analyze(content_items, time_window="24h")

    assert "catalysts" in result
    assert isinstance(result["catalysts"], list)
