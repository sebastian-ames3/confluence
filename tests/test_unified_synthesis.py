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


class TestContentDeduplication:
    """Tests for deduplication of content items by raw_content_id."""

    def test_dedup_prefers_transcript_harvester_over_classifier(self):
        """When both classifier and transcript_harvester exist, prefer transcript_harvester."""
        from backend.routes.synthesis import _get_content_for_synthesis
        from unittest.mock import MagicMock, patch

        # Create mock objects for two AnalyzedContent records with same raw_content_id
        classifier_analyzed = MagicMock()
        classifier_analyzed.agent_type = "classifier"
        classifier_analyzed.id = 1
        classifier_analyzed.key_themes = "theme1"
        classifier_analyzed.tickers_mentioned = ""
        classifier_analyzed.sentiment = "bullish"
        classifier_analyzed.conviction = "medium"
        classifier_analyzed.analysis_result = '{"summary": "classifier summary"}'

        transcript_analyzed = MagicMock()
        transcript_analyzed.agent_type = "transcript_harvester"
        transcript_analyzed.id = 2
        transcript_analyzed.key_themes = "theme1,theme2"
        transcript_analyzed.tickers_mentioned = "SPX"
        transcript_analyzed.sentiment = "bullish"
        transcript_analyzed.conviction = "high"
        transcript_analyzed.analysis_result = '{"summary": "rich transcript summary", "key_quotes": []}'

        raw = MagicMock()
        raw.id = 100
        raw.content_type = "video"
        raw.collected_at = datetime(2024, 1, 1)
        raw.content_text = "Full transcript text"
        raw.json_metadata = '{"title": "Test Video"}'

        source = MagicMock()
        source.name = "youtube"

        # Simulate query returning both records
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            (classifier_analyzed, raw, source),
            (transcript_analyzed, raw, source),
        ]

        cutoff = datetime(2024, 1, 1)
        result = _get_content_for_synthesis(mock_db, cutoff)

        # Should only have one item (deduplicated)
        assert len(result) == 1
        # Should prefer transcript_harvester (analyzed_content_id=2)
        assert result[0]["analyzed_content_id"] == 2

    def test_dedup_keeps_unique_raw_ids(self):
        """Items with different raw_content_ids should all be kept."""
        from backend.routes.synthesis import _get_content_for_synthesis

        analyzed1 = MagicMock()
        analyzed1.agent_type = "classifier"
        analyzed1.id = 1
        analyzed1.key_themes = ""
        analyzed1.tickers_mentioned = ""
        analyzed1.sentiment = ""
        analyzed1.conviction = ""
        analyzed1.analysis_result = '{"summary": "s1"}'

        analyzed2 = MagicMock()
        analyzed2.agent_type = "classifier"
        analyzed2.id = 2
        analyzed2.key_themes = ""
        analyzed2.tickers_mentioned = ""
        analyzed2.sentiment = ""
        analyzed2.conviction = ""
        analyzed2.analysis_result = '{"summary": "s2"}'

        raw1 = MagicMock()
        raw1.id = 100
        raw1.content_type = "article"
        raw1.collected_at = datetime(2024, 1, 1)
        raw1.content_text = "Content 1"
        raw1.json_metadata = '{"title": "Article 1"}'

        raw2 = MagicMock()
        raw2.id = 200
        raw2.content_type = "article"
        raw2.collected_at = datetime(2024, 1, 2)
        raw2.content_text = "Content 2"
        raw2.json_metadata = '{"title": "Article 2"}'

        source = MagicMock()
        source.name = "substack"

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            (analyzed1, raw1, source),
            (analyzed2, raw2, source),
        ]

        cutoff = datetime(2024, 1, 1)
        result = _get_content_for_synthesis(mock_db, cutoff)

        assert len(result) == 2


class TestAnalyzedSummaryHandling:
    """Tests for improved analyzed_summary usage in prompt building."""

    def test_stub_content_uses_analyzed_summary(self):
        """When content is a stub (<200 chars) and summary exists, use summary."""
        agent = SynthesisAgent()

        items = [{
            "title": "Test Video",
            "type": "video",
            "content_text": "Short title only",  # < 200 chars
            "analyzed_summary": "Detailed AI analysis of the video covering themes X, Y, Z.",
            "themes": ["rates", "inflation"],
            "summary": "",
            "sentiment": "",
            "key_quotes": [],
        }]

        prompt = agent._build_source_analysis_prompt("youtube:Moonshots", items, "7d")

        assert "[Pre-analyzed Summary]" in prompt
        assert "Detailed AI analysis" in prompt
        assert "Full content not available" in prompt
        # Should NOT have Full Content/Transcript
        assert "Full Content/Transcript" not in prompt

    def test_normal_content_includes_supplementary_summary(self):
        """When content is normal length and summary exists, include both."""
        agent = SynthesisAgent()

        items = [{
            "title": "Test Video",
            "type": "video",
            "content_text": "A" * 500,  # 500 chars, well within limits
            "analyzed_summary": "AI analysis summary.",
            "themes": [],
            "summary": "",
            "sentiment": "",
            "key_quotes": [],
        }]

        prompt = agent._build_source_analysis_prompt("youtube:Moonshots", items, "7d")

        assert "Full Content/Transcript" in prompt
        assert "[Supplementary AI Analysis]" in prompt
        assert "AI analysis summary." in prompt

    def test_long_content_uses_summary_only(self):
        """When content exceeds MAX_TRANSCRIPT_CHARS and summary exists, use summary."""
        agent = SynthesisAgent()

        items = [{
            "title": "Long Video",
            "type": "video",
            "content_text": "A" * 70000,  # > 60K default
            "analyzed_summary": "Summary of very long transcript.",
            "themes": ["macro"],
            "summary": "",
            "sentiment": "",
            "key_quotes": [],
        }]

        prompt = agent._build_source_analysis_prompt("youtube:Moonshots", items, "7d")

        assert "[Pre-analyzed Summary]" in prompt
        assert "Summary of very long transcript." in prompt
        assert "truncated" in prompt
        assert "Full Content/Transcript" not in prompt

    def test_no_summary_no_content_still_works(self):
        """When neither summary nor meaningful content exists, handle gracefully."""
        agent = SynthesisAgent()

        items = [{
            "title": "Empty Item",
            "type": "article",
            "content_text": "",
            "analyzed_summary": "",
            "themes": [],
            "summary": "",
            "sentiment": "",
            "key_quotes": [],
        }]

        prompt = agent._build_source_analysis_prompt("substack", items, "7d")

        # Should not crash, just include the title
        assert "Empty Item" in prompt


class TestPromptSizeGuard:
    """Tests for total prompt size guard per source."""

    def test_prompt_size_guard_truncates_excess_items(self):
        """When cumulative chars exceed MAX_SOURCE_PROMPT_CHARS, remaining items are omitted."""
        from agents.config import MAX_SOURCE_PROMPT_CHARS
        agent = SynthesisAgent()

        # Create items that will exceed the limit
        items = []
        for i in range(20):
            items.append({
                "title": f"Video {i}",
                "type": "video",
                "content_text": "X" * 50000,  # 50K per item, 20 items = 1M total
                "analyzed_summary": "",
                "themes": [],
                "summary": "",
                "sentiment": "",
                "key_quotes": [],
            })

        prompt = agent._build_source_analysis_prompt("youtube:Moonshots", items, "7d")

        # Should have the truncation note
        assert "additional items omitted" in prompt
        # Total prompt should be roughly within limits (plus the last oversized item)
        assert len(prompt) < MAX_SOURCE_PROMPT_CHARS * 2  # generous upper bound

    def test_prompt_size_guard_force_summary_mode(self):
        """When budget is low, items should switch to summary mode."""
        agent = SynthesisAgent()

        # Create items: first few large, last one should be force-summarized
        items = []
        # Fill up most of the budget
        for i in range(2):
            items.append({
                "title": f"Large Video {i}",
                "type": "video",
                "content_text": "Y" * 60000,
                "analyzed_summary": f"Summary of large video {i}.",
                "themes": ["theme"],
                "summary": "",
                "sentiment": "",
                "key_quotes": [],
            })
        # Add one more that should trigger force_summary
        items.append({
            "title": "Final Video",
            "type": "video",
            "content_text": "Z" * 40000,
            "analyzed_summary": "Summary of final video.",
            "themes": ["theme"],
            "summary": "",
            "sentiment": "",
            "key_quotes": [],
        })

        prompt = agent._build_source_analysis_prompt("youtube:Moonshots", items, "7d")

        # Should contain all three video titles (150K limit with 60K+60K+40K = 160K chars of content)
        assert "Large Video 0" in prompt
        assert "Large Video 1" in prompt
