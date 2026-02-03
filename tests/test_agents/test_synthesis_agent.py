"""
Tests for SynthesisAgent.

Uses mocked Claude responses to test synthesis logic.
"""

import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


# Sample Claude response for testing (matches new unified schema)
MOCK_SYNTHESIS_RESPONSE = {
    "executive_summary": {
        "macro_context": "Risk-on environment with improving growth indicators.",
        "synthesis_narrative": "Markets are showing clear risk-on sentiment with multiple sources highlighting the Fed pivot narrative.",
        "key_takeaways": [
            "42 Macro emphasizes improving growth indicators",
            "Options Insight notes increasing call skew in equities",
            "Confluence across macro data, positioning, and technicals"
        ],
        "overall_tone": "constructive",
        "dominant_theme": "Fed pivot"
    },
    "confluence_zones": [
        {
            "theme": "Fed pivot",
            "confluence_strength": 0.85,
            "sources_aligned": [
                {"source": "42macro", "view": "Rate cuts incoming"},
                {"source": "youtube:Forward Guidance", "view": "Dovish shift confirmed"}
            ]
        }
    ],
    "conflict_watch": [
        {
            "topic": "Duration positioning",
            "bull_case": {"view": "Bullish long end", "sources": ["42macro"]},
            "bear_case": {"view": "Cautious on rates", "sources": ["discord"]},
            "resolution_trigger": "Next CPI print"
        }
    ],
    "attention_priorities": [
        {
            "rank": 1,
            "focus_area": "Gold setup",
            "why": "Multiple sources cite declining real rates",
            "time_sensitivity": "high"
        }
    ],
    "catalyst_calendar": [
        {"date": "Dec 18", "event": "FOMC meeting", "impact": "high"},
        {"date": "Dec 11", "event": "CPI release", "impact": "high"}
    ],
    "re_review_recommendations": [],
    "market_regime": "risk-on"
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
    assert "research assistant" in agent.SYSTEM_PROMPT.lower()


def test_synthesis_generation(agent):
    """Test synthesis generates expected structure."""
    content_items = [
        {"source": "42macro", "summary": "Bullish on gold", "themes": ["gold", "rates"]},
        {"source": "discord", "summary": "Vol surface bullish", "themes": ["volatility"]}
    ]

    with patch.object(agent, 'call_claude', return_value=MOCK_SYNTHESIS_RESPONSE):
        result = agent.analyze(content_items, time_window="24h")

    assert "executive_summary" in result
    assert "confluence_zones" in result
    assert "conflict_watch" in result
    assert result["time_window"] == "24h"


def test_empty_content_handling(agent):
    """Test synthesis handles empty content gracefully."""
    result = agent.analyze([], time_window="24h")

    assert result["content_count"] == 0
    assert "executive_summary" in result


def test_confluence_zones_structure(agent):
    """Test confluence zones have proper structure."""
    content_items = [{"source": "42macro", "summary": "test"}]

    with patch.object(agent, 'call_claude', return_value=MOCK_SYNTHESIS_RESPONSE):
        result = agent.analyze(content_items, time_window="24h")

    assert "confluence_zones" in result
    if result["confluence_zones"]:
        zone = result["confluence_zones"][0]
        assert "theme" in zone
        assert "confluence_strength" in zone
        assert "sources_aligned" in zone


def test_executive_summary_tone(agent):
    """Test that executive summary includes overall tone."""
    content_items = [{"source": "42macro", "summary": "test"}]

    with patch.object(agent, 'call_claude', return_value=MOCK_SYNTHESIS_RESPONSE):
        result = agent.analyze(content_items, time_window="24h")

    assert "executive_summary" in result
    assert "overall_tone" in result["executive_summary"]


def test_conflict_watch_detected(agent):
    """Test conflicts are surfaced."""
    content_items = [
        {"source": "42macro", "summary": "Bullish bonds"},
        {"source": "discord", "summary": "Bearish bonds"}
    ]

    with patch.object(agent, 'call_claude', return_value=MOCK_SYNTHESIS_RESPONSE):
        result = agent.analyze(content_items, time_window="24h")

    assert "conflict_watch" in result


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

    assert "executive_summary" in result


def test_catalyst_calendar_included(agent):
    """Test catalyst calendar is included in output."""
    content_items = [{"source": "42macro", "summary": "FOMC upcoming"}]

    with patch.object(agent, 'call_claude', return_value=MOCK_SYNTHESIS_RESPONSE):
        result = agent.analyze(content_items, time_window="24h")

    assert "catalyst_calendar" in result
    assert isinstance(result["catalyst_calendar"], list)


def test_source_breakdowns_included(agent):
    """Test source breakdowns are in the output."""
    content_items = [{"source": "42macro", "summary": "test"}]

    with patch.object(agent, 'call_claude', return_value=MOCK_SYNTHESIS_RESPONSE):
        result = agent.analyze(content_items, time_window="24h")

    assert "source_breakdowns" in result
    assert isinstance(result["source_breakdowns"], dict)


def test_content_summaries_included(agent):
    """Test content summaries are in the output."""
    content_items = [{"source": "42macro", "summary": "test"}]

    with patch.object(agent, 'call_claude', return_value=MOCK_SYNTHESIS_RESPONSE):
        result = agent.analyze(content_items, time_window="24h")

    assert "content_summaries" in result
    assert isinstance(result["content_summaries"], list)
