"""
Unit Tests for Content Classifier Agent

Tests classification logic, priority rules, and routing decisions.
"""

import pytest
import os
import json
from unittest.mock import Mock, patch
from agents.content_classifier import ContentClassifierAgent


class TestContentClassifierAgent:
    """Test suite for ContentClassifierAgent."""

    @pytest.fixture
    def agent(self):
        """Create a ContentClassifierAgent instance for testing."""
        # Mock the Anthropic client to avoid initialization issues in tests
        with patch('agents.base_agent.Anthropic'):
            with patch.dict('os.environ', {'CLAUDE_API_KEY': 'test-key'}):
                return ContentClassifierAgent(api_key='test-key')

    @pytest.fixture
    def mock_claude_response(self):
        """Mock Claude API response."""
        return {
            "classification": "simple_text",
            "detected_topics": ["Federal Reserve", "Interest Rates", "Tech Sector"],
            "information_density": "high",
            "actionability": "medium",
            "confidence": 0.92
        }

    # ========================================================================
    # Priority Rules Tests
    # ========================================================================

    def test_high_priority_discord_video(self, agent):
        """Test that Discord video links get high priority."""
        raw_content = {
            "raw_content_id": 1,
            "source": "discord",
            "content_type": "video",
            "url": "https://zoom.us/rec/play/abc123",
            "content_text": "Imran's analysis on market conditions",
            "metadata": {"channel": "stocks-chat"}
        }

        claude_response = {
            "classification": "transcript_needed",
            "detected_topics": ["SPY", "VIX"],
            "information_density": "high",
            "actionability": "high",
            "confidence": 0.95
        }

        priority = agent._determine_priority(raw_content, claude_response)
        assert priority == "high"

    def test_high_priority_42macro_leadoff(self, agent):
        """Test that 42macro Leadoff Morning Note gets high priority."""
        raw_content = {
            "raw_content_id": 2,
            "source": "42macro",
            "content_type": "pdf",
            "content_text": "Leadoff Morning Note - Market analysis for today",
            "file_path": "/pdfs/leadoff_2025_01_18.pdf",
            "metadata": {}
        }

        claude_response = {
            "classification": "pdf_analysis",
            "detected_topics": ["Macro regime", "GDP"],
            "information_density": "high",
            "actionability": "high",
            "confidence": 0.90
        }

        priority = agent._determine_priority(raw_content, claude_response)
        assert priority == "high"

    def test_high_priority_twitter_trade_setup(self, agent):
        """Test that Twitter trade setups get high priority."""
        raw_content = {
            "raw_content_id": 3,
            "source": "twitter",
            "content_type": "text",
            "content_text": "KTTECHPRIVATE: New trade setup - Long SPY at 580, stop loss at 575, target 590",
            "url": "https://twitter.com/KTTECHPRIVATE/status/123",
            "metadata": {"author": "KTTECHPRIVATE"}
        }

        claude_response = {
            "classification": "simple_text",
            "detected_topics": ["SPY", "Trade Setup"],
            "information_density": "high",
            "actionability": "high",
            "confidence": 0.98
        }

        priority = agent._determine_priority(raw_content, claude_response)
        assert priority == "high"

    def test_medium_priority_42macro_weekly(self, agent):
        """Test that 42macro weekly reports get medium priority."""
        raw_content = {
            "raw_content_id": 4,
            "source": "42macro",
            "content_type": "pdf",
            "content_text": "Macro Scouting Report - Weekly analysis",
            "file_path": "/pdfs/macro_scouting_2025_01_18.pdf",
            "metadata": {}
        }

        claude_response = {
            "classification": "pdf_analysis",
            "detected_topics": ["Macro trends"],
            "information_density": "medium",
            "actionability": "medium",
            "confidence": 0.85
        }

        priority = agent._determine_priority(raw_content, claude_response)
        assert priority == "medium"

    def test_medium_priority_youtube(self, agent):
        """Test that YouTube videos get medium priority by default."""
        raw_content = {
            "raw_content_id": 5,
            "source": "youtube",
            "content_type": "video",
            "url": "https://www.youtube.com/watch?v=abc123",
            "content_text": "Long-form macro discussion with economist",
            "metadata": {"channel": "Forward Guidance"}
        }

        claude_response = {
            "classification": "transcript_needed",
            "detected_topics": ["Economic outlook"],
            "information_density": "medium",
            "actionability": "low",
            "confidence": 0.80
        }

        priority = agent._determine_priority(raw_content, claude_response)
        assert priority == "medium"

    def test_low_priority_general_commentary(self, agent):
        """Test that general commentary gets low priority."""
        raw_content = {
            "raw_content_id": 6,
            "source": "twitter",
            "content_type": "text",
            "content_text": "Markets looking interesting today. Watching for developments.",
            "url": "https://twitter.com/random/status/456",
            "metadata": {}
        }

        claude_response = {
            "classification": "simple_text",
            "detected_topics": ["Markets"],
            "information_density": "low",
            "actionability": "low",
            "confidence": 0.70
        }

        priority = agent._determine_priority(raw_content, claude_response)
        assert priority == "low"

    # ========================================================================
    # Routing Logic Tests
    # ========================================================================

    def test_routing_video_content(self, agent):
        """Test routing for video content."""
        raw_content = {
            "content_type": "video",
            "url": "https://youtube.com/watch?v=xyz"
        }

        claude_response = {
            "classification": "transcript_needed",
            "information_density": "high"
        }

        routing = agent._determine_routing(raw_content, claude_response)
        assert "transcript_harvester" in routing
        assert "confluence_scorer" in routing

    def test_routing_pdf_content(self, agent):
        """Test routing for PDF content."""
        raw_content = {
            "content_type": "pdf",
            "file_path": "/pdfs/report.pdf"
        }

        claude_response = {
            "classification": "pdf_analysis",
            "information_density": "high"
        }

        routing = agent._determine_routing(raw_content, claude_response)
        assert "pdf_analyzer" in routing
        assert "confluence_scorer" in routing

    def test_routing_image_content(self, agent):
        """Test routing for image content."""
        raw_content = {
            "content_type": "image",
            "file_path": "/images/chart.png"
        }

        claude_response = {
            "classification": "image_intelligence",
            "information_density": "medium"
        }

        routing = agent._determine_routing(raw_content, claude_response)
        assert "image_intelligence" in routing
        assert "confluence_scorer" in routing

    def test_routing_high_density_text(self, agent):
        """Test routing for high-density text content."""
        raw_content = {
            "content_type": "text",
            "content_text": "Detailed analysis of Fed policy..."
        }

        claude_response = {
            "classification": "simple_text",
            "information_density": "high"
        }

        routing = agent._determine_routing(raw_content, claude_response)
        assert "confluence_scorer" in routing
        assert "transcript_harvester" not in routing

    def test_routing_low_density_text_archive_only(self, agent):
        """Test that low-density text marked as archive_only gets no routing."""
        raw_content = {
            "content_type": "text",
            "content_text": "Random thoughts..."
        }

        claude_response = {
            "classification": "archive_only",
            "information_density": "low"
        }

        routing = agent._determine_routing(raw_content, claude_response)
        assert len(routing) == 0

    # ========================================================================
    # Processing Time Estimation Tests
    # ========================================================================

    def test_estimate_processing_time_video(self, agent):
        """Test processing time estimation for video."""
        raw_content = {"content_type": "video"}
        route_to_agents = ["transcript_harvester", "confluence_scorer"]

        time = agent._estimate_processing_time(raw_content, route_to_agents)
        assert time == 190  # 180 + 10

    def test_estimate_processing_time_pdf(self, agent):
        """Test processing time estimation for PDF."""
        raw_content = {"content_type": "pdf"}
        route_to_agents = ["pdf_analyzer", "confluence_scorer"]

        time = agent._estimate_processing_time(raw_content, route_to_agents)
        assert time == 40  # 30 + 10

    def test_estimate_processing_time_text_only(self, agent):
        """Test processing time estimation for text only."""
        raw_content = {"content_type": "text"}
        route_to_agents = ["confluence_scorer"]

        time = agent._estimate_processing_time(raw_content, route_to_agents)
        assert time == 10

    # ========================================================================
    # Fallback Classification Tests
    # ========================================================================

    def test_fallback_video(self, agent):
        """Test fallback classification for video."""
        raw_content = {
            "raw_content_id": 10,
            "content_type": "video",
            "url": "https://youtube.com/watch?v=test"
        }

        result = agent._fallback_classification(raw_content)
        assert result["classification"] == "transcript_needed"
        assert result["priority"] == "medium"
        assert "transcript_harvester" in result["route_to_agents"]
        assert result["confidence"] == 0.3

    def test_fallback_pdf(self, agent):
        """Test fallback classification for PDF."""
        raw_content = {
            "raw_content_id": 11,
            "content_type": "pdf",
            "file_path": "/test.pdf"
        }

        result = agent._fallback_classification(raw_content)
        assert result["classification"] == "pdf_analysis"
        assert "pdf_analyzer" in result["route_to_agents"]

    def test_fallback_text(self, agent):
        """Test fallback classification for text."""
        raw_content = {
            "raw_content_id": 12,
            "content_type": "text",
            "content_text": "Some text"
        }

        result = agent._fallback_classification(raw_content)
        assert result["classification"] == "simple_text"
        assert "confluence_scorer" in result["route_to_agents"]

    # ========================================================================
    # Integration Tests with Mocked Claude API
    # ========================================================================

    @patch('agents.base_agent.BaseAgent.call_claude')
    def test_classify_success(self, mock_call_claude, agent, mock_claude_response):
        """Test successful classification with mocked Claude API."""
        mock_call_claude.return_value = mock_claude_response

        raw_content = {
            "raw_content_id": 20,
            "source": "42macro",
            "content_type": "text",
            "content_text": "Federal Reserve maintains hawkish stance on inflation...",
            "metadata": {}
        }

        result = agent.classify(raw_content)

        assert result["classification"] == "simple_text"
        assert result["priority"] in ["high", "medium", "low"]
        assert "detected_topics" in result
        assert result["confidence"] == 0.92
        assert len(result["route_to_agents"]) > 0

    @patch('agents.base_agent.BaseAgent.call_claude')
    def test_classify_handles_api_failure(self, mock_call_claude, agent):
        """Test that classify() handles Claude API failures gracefully."""
        mock_call_claude.side_effect = Exception("API Error")

        raw_content = {
            "raw_content_id": 21,
            "source": "discord",
            "content_type": "text",
            "content_text": "Test content",
            "metadata": {}
        }

        result = agent.classify(raw_content)

        # Should return fallback classification
        assert result["classification"] in ["simple_text", "transcript_needed", "pdf_analysis", "image_intelligence"]
        assert result["confidence"] == 0.3
        assert "fallback" in result["raw_analysis"]

    @patch('agents.base_agent.BaseAgent.call_claude')
    def test_classify_validates_response_schema(self, mock_call_claude, agent):
        """Test that classify() validates Claude response schema."""
        # Missing required fields
        mock_call_claude.return_value = {
            "classification": "simple_text"
            # Missing: detected_topics, confidence
        }

        raw_content = {
            "raw_content_id": 22,
            "source": "twitter",
            "content_type": "text",
            "content_text": "Test",
            "metadata": {}
        }

        # Should catch validation error and return fallback
        result = agent.classify(raw_content)
        assert "fallback" in result["raw_analysis"]

    # ========================================================================
    # Edge Cases
    # ========================================================================

    def test_empty_content_text(self, agent):
        """Test handling of empty content text."""
        raw_content = {
            "raw_content_id": 30,
            "source": "discord",
            "content_type": "text",
            "content_text": "",
            "metadata": {}
        }

        prompt = agent._build_classification_prompt(raw_content)
        assert "Content Preview" in prompt
        assert "discord" in prompt

    def test_none_content_text(self, agent):
        """Test handling of None content text."""
        raw_content = {
            "raw_content_id": 31,
            "source": "discord",
            "content_type": "text",
            "content_text": None,
            "metadata": {}
        }

        prompt = agent._build_classification_prompt(raw_content)
        assert prompt is not None

    def test_long_content_truncation(self, agent):
        """Test that long content gets truncated in prompt."""
        long_text = "A" * 2000  # 2000 characters

        raw_content = {
            "raw_content_id": 32,
            "source": "substack",
            "content_type": "text",
            "content_text": long_text,
            "metadata": {}
        }

        prompt = agent._build_classification_prompt(raw_content)
        # Should only include first 1000 chars in preview
        assert len(raw_content["content_text"]) == 2000
        assert long_text[:1000] in prompt


# ============================================================================
# Integration Test with Real API (Optional - requires API key)
# ============================================================================

@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("CLAUDE_API_KEY"),
    reason="Integration tests require CLAUDE_API_KEY environment variable"
)
class TestContentClassifierIntegration:
    """
    Integration tests with real Claude API.

    Run with: pytest -m integration
    Requires CLAUDE_API_KEY environment variable.
    """

    @pytest.fixture
    def agent(self):
        """Create agent with real API key."""
        return ContentClassifierAgent()

    def test_real_classification_42macro(self, agent):
        """Test classification with real Claude API - 42macro content."""
        raw_content = {
            "raw_content_id": 100,
            "source": "42macro",
            "content_type": "text",
            "content_text": """
            The Federal Reserve's recent hawkish stance on inflation continues to
            dominate market sentiment. Core PCE remains elevated at 2.8% YoY,
            suggesting limited room for rate cuts in Q1. Tech sector rotation
            accelerating as investors seek defensive positioning ahead of earnings.
            """,
            "metadata": {"date": "2025-01-18"}
        }

        result = agent.classify(raw_content)

        assert result["classification"] in ["simple_text", "archive_only"]
        assert result["priority"] in ["high", "medium", "low"]
        assert len(result["detected_topics"]) > 0
        assert result["confidence"] > 0.5
        assert "Federal Reserve" in str(result["detected_topics"]) or "Fed" in str(result["detected_topics"])


