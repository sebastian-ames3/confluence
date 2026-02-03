"""
Tests for Synthesis Pipeline

Tests for the unified synthesis pipeline:
- Empty synthesis structure
- Source key extraction with YouTube channel granularity
- Content summary generation
- Source breakdown prompt building
"""

import pytest
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

# Set a dummy API key for testing (agent won't make real calls)
os.environ["CLAUDE_API_KEY"] = "test-dummy-key-for-testing"

# Test imports
from agents.synthesis_agent import SynthesisAgent


class TestEmptySynthesisSchema:
    """Tests for empty synthesis structure."""

    def test_empty_synthesis_structure(self):
        """Empty synthesis should have correct structure."""
        agent = SynthesisAgent()
        result = agent._empty_synthesis("24h")

        assert "executive_summary" in result
        assert "confluence_zones" in result
        assert "conflict_watch" in result
        assert "attention_priorities" in result
        assert "catalyst_calendar" in result
        assert "re_review_recommendations" in result
        assert "source_breakdowns" in result
        assert "content_summaries" in result
        assert result["content_count"] == 0
        assert result["time_window"] == "24h"

    def test_empty_synthesis_has_all_required_keys(self):
        """Empty synthesis should have all required keys."""
        agent = SynthesisAgent()
        result = agent._empty_synthesis("7d")

        required_keys = [
            "executive_summary", "confluence_zones", "conflict_watch",
            "attention_priorities", "catalyst_calendar", "re_review_recommendations",
            "source_breakdowns", "content_summaries", "content_count",
            "sources_included", "time_window", "generated_at"
        ]
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"


class TestSourceKeyExtraction:
    """Tests for source key generation with YouTube channel granularity."""

    def test_get_source_key_regular_source(self):
        """Regular sources should return source name."""
        agent = SynthesisAgent()

        item = {"source": "42macro"}
        assert agent._get_source_key(item) == "42macro"

        item = {"source": "discord"}
        assert agent._get_source_key(item) == "discord"

    def test_get_source_key_youtube_with_channel(self):
        """YouTube with channel should return youtube:channel."""
        agent = SynthesisAgent()

        item = {"source": "youtube", "channel_display": "Moonshots"}
        assert agent._get_source_key(item) == "youtube:Moonshots"

        item = {"source": "youtube", "channel_display": "Forward Guidance"}
        assert agent._get_source_key(item) == "youtube:Forward Guidance"

    def test_get_source_key_youtube_without_channel(self):
        """YouTube without channel should return just youtube."""
        agent = SynthesisAgent()

        item = {"source": "youtube"}
        assert agent._get_source_key(item) == "youtube"


class TestContentSummaryGeneration:
    """Tests for content summary generation."""

    def test_generate_content_summaries_basic(self):
        """Content summaries should include required fields."""
        agent = SynthesisAgent()

        items = [
            {
                "id": 1,
                "source": "youtube",
                "channel_display": "Moonshots",
                "title": "AI Revolution",
                "collected_at": "2025-12-25T10:00:00",
                "type": "video",
                "summary": "Discussion about AI trends.",
                "themes": ["AI", "technology"],
                "tickers": ["NVDA"],
                "sentiment": "bullish"
            }
        ]

        summaries = agent._generate_content_summaries(items)

        assert len(summaries) == 1
        assert summaries[0]["id"] == 1
        assert summaries[0]["source"] == "youtube"
        assert summaries[0]["channel"] == "Moonshots"
        assert summaries[0]["title"] == "AI Revolution"

    def test_generate_content_summaries_preserves_metadata(self):
        """Content summaries should preserve key metadata."""
        agent = SynthesisAgent()

        items = [
            {
                "id": 2,
                "source": "42macro",
                "title": "Macro Report",
                "content_type": "pdf",
                "themes": ["rates", "fed"],
                "tickers": ["SPX", "TLT"],
                "sentiment": "neutral"
            }
        ]

        summaries = agent._generate_content_summaries(items)

        assert summaries[0]["themes"] == ["rates", "fed"]
        assert summaries[0]["tickers_mentioned"] == ["SPX", "TLT"]
        assert summaries[0]["sentiment"] == "neutral"

    def test_generate_content_summaries_handles_missing_fields(self):
        """Content summaries should handle missing optional fields."""
        agent = SynthesisAgent()

        items = [
            {"id": 3, "source": "substack"}
        ]

        summaries = agent._generate_content_summaries(items)

        assert summaries[0]["id"] == 3
        assert summaries[0]["title"] == "Untitled"
        assert summaries[0]["themes"] == []


class TestSourceAnalysisPrompt:
    """Tests for source analysis prompt building."""

    def test_build_source_analysis_prompt_includes_source(self):
        """Prompt should include source name."""
        agent = SynthesisAgent()

        items = [
            {"source": "42macro", "title": "Report 1", "summary": "Test content"}
        ]

        prompt = agent._build_source_analysis_prompt("42macro", items, "7d")

        assert "42macro" in prompt
        assert "Report 1" in prompt

    def test_build_source_analysis_prompt_includes_content(self):
        """Prompt should include item content."""
        agent = SynthesisAgent()

        items = [
            {"source": "discord", "title": "Trade Idea", "summary": "Long SPX", "content_text": "Detailed trade thesis"}
        ]

        prompt = agent._build_source_analysis_prompt("discord", items, "24h")

        assert "discord" in prompt
        assert "Trade Idea" in prompt


class TestYouTubeChannelGranularity:
    """Tests for YouTube channel-level breakdowns."""

    def test_youtube_channels_tracked_separately(self):
        """Each YouTube channel should be tracked as separate source."""
        agent = SynthesisAgent()

        items = [
            {"source": "youtube", "channel_display": "Moonshots", "title": "Video 1"},
            {"source": "youtube", "channel_display": "Moonshots", "title": "Video 2"},
            {"source": "youtube", "channel_display": "Forward Guidance", "title": "Video 3"},
        ]

        # Group by source key
        groups = {}
        for item in items:
            key = agent._get_source_key(item)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)

        assert "youtube:Moonshots" in groups
        assert "youtube:Forward Guidance" in groups
        assert len(groups["youtube:Moonshots"]) == 2
        assert len(groups["youtube:Forward Guidance"]) == 1
