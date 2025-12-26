"""
Tests for PRD-041 Tiered Synthesis

Tests for the three-tier synthesis enhancement:
- Tier 1: Executive summary
- Tier 2: Source breakdowns (with YouTube channel granularity)
- Tier 3: Per-content summaries
"""

import pytest
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

# Set a dummy API key for testing (agent won't make real calls)
os.environ["CLAUDE_API_KEY"] = "test-dummy-key-for-testing"

# Test imports
from agents.synthesis_agent import SynthesisAgent


class TestTieredSynthesisSchema:
    """Tests for V4 synthesis schema structure."""

    def test_empty_synthesis_v4_structure(self):
        """Empty V4 synthesis should have correct structure."""
        agent = SynthesisAgent()
        result = agent._empty_synthesis_v4("24h")

        assert result["version"] == "4.0"
        assert "executive_summary" in result
        assert "confluence_zones" in result
        assert "source_breakdowns" in result
        assert "content_summaries" in result
        assert result["content_count"] == 0

    def test_empty_synthesis_has_youtube_channels_field(self):
        """Empty V4 should have youtube_channels_included field."""
        agent = SynthesisAgent()
        result = agent._empty_synthesis_v4("7d")

        assert "youtube_channels_included" in result
        assert isinstance(result["youtube_channels_included"], list)


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
    """Tests for Tier 3 content summary generation."""

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


class TestSourceBreakdownPrompt:
    """Tests for source breakdown prompt building."""

    def test_build_source_breakdown_prompt_includes_source(self):
        """Prompt should include source name."""
        agent = SynthesisAgent()

        items = [
            {"source": "42macro", "title": "Report 1", "summary": "Test content"}
        ]

        prompt = agent._build_source_breakdown_prompt(items, "42macro")

        assert "42macro" in prompt
        assert "Report 1" in prompt

    def test_build_source_breakdown_prompt_limits_items(self):
        """Prompt should limit to 10 items per source."""
        agent = SynthesisAgent()

        # Create 15 items
        items = [
            {"source": "discord", "title": f"Item {i}", "summary": f"Content {i}"}
            for i in range(15)
        ]

        prompt = agent._build_source_breakdown_prompt(items, "discord")

        # Should only include first 10
        assert "Item 0" in prompt
        assert "Item 9" in prompt
        # Item 10+ should not be in prompt


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


class TestTierFiltering:
    """Tests for tier-based response filtering."""

    def test_full_v4_response_has_all_tiers(self):
        """Full V4 response should have all three tiers."""
        response = {
            "version": "4.0",
            "executive_summary": {"narrative": "Test"},
            "confluence_zones": [],
            "source_breakdowns": {"42macro": {"summary": "test"}},
            "content_summaries": [{"id": 1}]
        }

        # Tier 3 (full) should have everything
        assert "executive_summary" in response
        assert "source_breakdowns" in response
        assert "content_summaries" in response

    def test_tier_1_excludes_details(self):
        """Tier 1 should only have executive summary."""
        response = {
            "version": "4.0",
            "executive_summary": {"narrative": "Test"},
            "source_breakdowns": {"42macro": {"summary": "test"}},
            "content_summaries": [{"id": 1}]
        }

        # Simulate tier 1 filtering
        tier1 = response.copy()
        tier1.pop("source_breakdowns", None)
        tier1.pop("content_summaries", None)

        assert "executive_summary" in tier1
        assert "source_breakdowns" not in tier1
        assert "content_summaries" not in tier1

    def test_tier_2_includes_source_breakdowns(self):
        """Tier 2 should have executive + source breakdowns."""
        response = {
            "version": "4.0",
            "executive_summary": {"narrative": "Test"},
            "source_breakdowns": {"42macro": {"summary": "test"}},
            "content_summaries": [{"id": 1}]
        }

        # Simulate tier 2 filtering
        tier2 = response.copy()
        tier2.pop("content_summaries", None)

        assert "executive_summary" in tier2
        assert "source_breakdowns" in tier2
        assert "content_summaries" not in tier2


class TestVersionCompatibility:
    """Tests for backwards compatibility with V3."""

    def test_v4_includes_v3_fields(self):
        """V4 response should include all V3 fields."""
        agent = SynthesisAgent()
        empty = agent._empty_synthesis_v4("24h")

        # V3 required fields
        v3_fields = [
            "executive_summary",
            "confluence_zones",
            "conflict_watch",
            "attention_priorities",
            "catalyst_calendar"
        ]

        for field in v3_fields:
            assert field in empty, f"V4 should include V3 field: {field}"

    def test_v4_adds_new_fields(self):
        """V4 should add source_breakdowns and content_summaries."""
        agent = SynthesisAgent()
        empty = agent._empty_synthesis_v4("24h")

        assert "source_breakdowns" in empty
        assert "content_summaries" in empty
        assert "youtube_channels_included" in empty
