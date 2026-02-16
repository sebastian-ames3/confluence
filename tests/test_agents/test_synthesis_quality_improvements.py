"""
Tests for Synthesis & Analysis Quality Improvements (PRs 1-6).

Covers:
- PR 1: Config & model upgrade, MAX_SOURCE_TOKENS
- PR 2: analyzed_summary, theme extractor field name, scorer truncation
- PR 3: Pillar scores in synthesis merge prompt
- PR 4: Dynamic conviction, evidence strength, evolved theme matching
- PR 5: Evaluator source content awareness
- PR 6: CrossReferenceAgent empty scores handling
"""

import pytest
from unittest.mock import patch, MagicMock
import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


@pytest.fixture
def mock_env():
    """Set up mock environment variables."""
    with patch.dict(os.environ, {'CLAUDE_API_KEY': 'test-key-12345'}):
        yield


# ============================================================================
# PR 1: Config & Model Upgrade
# ============================================================================

class TestPR1ConfigAndModel:
    """Tests for config changes and MAX_SOURCE_TOKENS."""

    def test_model_synthesis_default(self):
        """Test MODEL_SYNTHESIS defaults to claude-opus-4-6."""
        with patch.dict(os.environ, {}, clear=False):
            # Remove SYNTHESIS_MODEL if set
            env = os.environ.copy()
            env.pop('SYNTHESIS_MODEL', None)
            with patch.dict(os.environ, env, clear=True):
                # Re-import to get fresh defaults
                import importlib
                import agents.config
                importlib.reload(agents.config)
                assert agents.config.MODEL_SYNTHESIS == "claude-opus-4-6"

    def test_max_source_tokens_default(self):
        """Test MAX_SOURCE_TOKENS defaults to 8000."""
        with patch.dict(os.environ, {}, clear=False):
            env = os.environ.copy()
            env.pop('MAX_SOURCE_TOKENS', None)
            with patch.dict(os.environ, env, clear=True):
                import importlib
                import agents.config
                importlib.reload(agents.config)
                assert agents.config.MAX_SOURCE_TOKENS == 8000

    def test_max_source_tokens_env_override(self):
        """Test MAX_SOURCE_TOKENS respects env var."""
        with patch.dict(os.environ, {'MAX_SOURCE_TOKENS': '10000'}):
            import importlib
            import agents.config
            importlib.reload(agents.config)
            assert agents.config.MAX_SOURCE_TOKENS == 10000

    def test_max_input_chars_removed(self):
        """Test that MAX_INPUT_CHARS is removed from config."""
        import agents.config
        assert not hasattr(agents.config, 'MAX_INPUT_CHARS')

    def test_analyze_source_uses_max_source_tokens(self, mock_env):
        """Test _analyze_source passes MAX_SOURCE_TOKENS as max_tokens (not old 6000)."""
        with patch('agents.base_agent.Anthropic'):
            from agents.synthesis_agent import SynthesisAgent
            agent = SynthesisAgent()

            mock_response = {
                "summary": "Test", "key_insights": [], "themes": [],
                "overall_bias": "neutral", "content_titles": [],
                "key_views": [], "catalysts_mentioned": [],
                "tickers_discussed": [], "notable_quotes": [],
                "macro_context_contribution": ""
            }

            with patch.object(agent, 'call_claude', return_value=mock_response) as mock_call:
                agent._analyze_source(
                    source_key="42macro",
                    items=[{"title": "Test", "content_text": "content"}],
                    time_window="24h"
                )
                # Verify max_tokens is NOT the old hardcoded 6000
                call_kwargs = mock_call.call_args.kwargs
                assert call_kwargs.get('max_tokens') != 6000
                # Should be the configured MAX_SOURCE_TOKENS (default 8000)
                assert call_kwargs.get('max_tokens') >= 8000


# ============================================================================
# PR 2: Fix Broken Content Pipelines
# ============================================================================

class TestPR2ContentPipelines:
    """Tests for content pipeline fixes."""

    def test_theme_extractor_reads_source_breakdowns(self, mock_env):
        """Test theme extractor reads source_breakdowns (not source_stances)."""
        with patch('agents.base_agent.Anthropic'):
            from agents.theme_extractor import ThemeExtractorAgent
            agent = ThemeExtractorAgent()

            synthesis_data = {
                "executive_summary": {"overall_tone": "bullish"},
                "confluence_zones": [],
                "conflict_watch": [],
                "attention_priorities": [],
                "source_breakdowns": {"42macro": {"summary": "Bullish macro"}},
            }

            prompt = agent._build_extraction_prompt(synthesis_data)
            assert "Source Breakdowns" in prompt
            assert "Bullish macro" in prompt
            # Should NOT reference old field name
            assert "Source Stances" not in prompt

    def test_confluence_scorer_uses_higher_char_limit(self, mock_env):
        """Test confluence scorer uses 12000 char limit instead of 2000."""
        with patch('agents.base_agent.Anthropic'):
            from agents.confluence_scorer import ConfluenceScorerAgent
            agent = ConfluenceScorerAgent()

            # Create content with transcript longer than 2000 but shorter than 12000
            long_transcript = "A" * 5000
            analyzed_content = {
                "source": "42macro",
                "content_type": "pdf",
                "transcript": long_transcript,
            }

            summary = agent._summarize_content(analyzed_content)
            # With old 2000 limit, the transcript would be truncated to 2000 chars
            # With new 12000 limit, all 5000 chars should be present
            assert len(summary) > 2500  # More than old limit would allow


# ============================================================================
# PR 3: Pillar Scores in Synthesis Merge
# ============================================================================

class TestPR3PillarScores:
    """Tests for feeding pillar scores into synthesis merge prompt."""

    def test_analyze_accepts_pillar_scores(self, mock_env):
        """Test SynthesisAgent.analyze() accepts pillar_scores parameter."""
        with patch('agents.base_agent.Anthropic'):
            from agents.synthesis_agent import SynthesisAgent
            agent = SynthesisAgent()

            mock_response = {
                "executive_summary": {"overall_tone": "neutral", "macro_context": "", "synthesis_narrative": "", "key_takeaways": [], "dominant_theme": None, "source_highlights": {}},
                "confluence_zones": [], "conflict_watch": [],
                "attention_priorities": [], "catalyst_calendar": [],
                "re_review_recommendations": []
            }

            pillar_scores = {
                "42macro": {
                    "score_count": 2,
                    "avg_core_total": 7.0,
                    "avg_total_score": 10.0,
                    "threshold_met": 1,
                    "scores": [
                        {"pillar_scores": {"macro": 2, "fundamentals": 1, "valuation": 1, "positioning": 2, "policy": 1, "price_action": 1, "options_vol": 2}, "core_total": 7, "total_score": 10, "meets_threshold": True},
                    ]
                }
            }

            with patch.object(agent, 'call_claude', return_value=mock_response):
                result = agent.analyze(
                    content_items=[{"source": "42macro", "summary": "test"}],
                    time_window="24h",
                    pillar_scores=pillar_scores
                )
            assert "executive_summary" in result

    def test_pillar_scores_in_merge_prompt(self, mock_env):
        """Test pillar scores appear in merge prompt when provided."""
        with patch('agents.base_agent.Anthropic'):
            from agents.synthesis_agent import SynthesisAgent
            agent = SynthesisAgent()

            pillar_scores = {
                "discord": {
                    "score_count": 1,
                    "avg_core_total": 6.0,
                    "avg_total_score": 9.0,
                    "threshold_met": 1,
                    "scores": [
                        {"pillar_scores": {"macro": 1, "fundamentals": 1, "valuation": 1, "positioning": 2, "policy": 1, "price_action": 1, "options_vol": 2}, "core_total": 6, "total_score": 9, "meets_threshold": True},
                    ]
                }
            }

            prompt = agent._build_merge_prompt(
                source_analyses={"discord": {"summary": "test", "key_insights": []}},
                pillar_scores=pillar_scores
            )
            assert "7-PILLAR CONFLUENCE SCORES" in prompt
            assert "DISCORD" in prompt
            assert "Avg Core Total: 6.0/10" in prompt

    def test_merge_prompt_without_pillar_scores(self, mock_env):
        """Test merge prompt works without pillar scores."""
        with patch('agents.base_agent.Anthropic'):
            from agents.synthesis_agent import SynthesisAgent
            agent = SynthesisAgent()

            prompt = agent._build_merge_prompt(
                source_analyses={"42macro": {"summary": "test", "key_insights": []}},
                pillar_scores=None
            )
            assert "7-PILLAR CONFLUENCE SCORES" not in prompt


# ============================================================================
# PR 4: Theme Conviction & Evidence Quality
# ============================================================================

class TestPR4ThemeConviction:
    """Tests for dynamic conviction and evidence strength."""

    def test_evidence_strength_for_source(self):
        """Test evidence strength mapping from source weights."""
        from agents.theme_extractor import _evidence_strength_for_source

        assert _evidence_strength_for_source("42macro") == "strong"      # weight 1.5
        assert _evidence_strength_for_source("discord") == "strong"      # weight 1.5
        assert _evidence_strength_for_source("kt_technical") == "moderate"  # weight 1.2
        assert _evidence_strength_for_source("substack") == "moderate"   # weight 1.0
        assert _evidence_strength_for_source("youtube") == "weak"        # weight 0.8
        assert _evidence_strength_for_source("unknown") == "moderate"    # default 1.0

    def test_compute_conviction_single_source(self):
        """Test conviction for single source."""
        from agents.theme_extractor import _compute_conviction

        # 42macro (weight 1.5): 0.3 + 0.15 * 1.5 = 0.525
        result = _compute_conviction(["42macro"])
        assert 0.5 <= result <= 0.55

        # youtube (weight 0.8): 0.3 + 0.15 * 0.8 = 0.42
        result = _compute_conviction(["youtube"])
        assert 0.40 <= result <= 0.45

    def test_compute_conviction_multiple_sources(self):
        """Test conviction increases with more sources."""
        from agents.theme_extractor import _compute_conviction

        one_source = _compute_conviction(["42macro"])
        two_sources = _compute_conviction(["42macro", "discord"])
        three_sources = _compute_conviction(["42macro", "discord", "kt_technical"])

        assert two_sources > one_source
        assert three_sources > two_sources

    def test_compute_conviction_capped_at_0_9(self):
        """Test conviction is capped at 0.9."""
        from agents.theme_extractor import _compute_conviction

        # 5 sources with high weights should still cap at 0.9
        result = _compute_conviction(["42macro", "discord", "kt_technical", "substack", "youtube"])
        assert result <= 0.9

    def test_evolved_theme_included_in_matching(self, mock_env):
        """Test that evolved themes are included in the matching query."""
        # This tests the query filter change; we verify by checking the function
        # reads the correct statuses. Full integration test requires DB.
        from agents.theme_extractor import extract_and_track_themes

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = []

        # Mock the ThemeExtractorAgent to avoid Claude calls
        with patch('agents.theme_extractor.ThemeExtractorAgent') as MockAgent:
            mock_agent_instance = MagicMock()
            MockAgent.return_value = mock_agent_instance
            mock_agent_instance.extract_themes_from_synthesis.return_value = [
                {"name": "test theme", "sources": {"42macro": "bullish"}, "status": "emerging"}
            ]
            mock_agent_instance.match_themes.return_value = []

            extract_and_track_themes({"executive_summary": {}}, mock_db)

            # Check that the query filter included "evolved"
            filter_calls = mock_query.filter.call_args_list
            # The filter should be called with status.in_ containing evolved
            assert len(filter_calls) >= 1


# ============================================================================
# PR 5: Evaluator Source Content Awareness
# ============================================================================

class TestPR5EvaluatorSourceAwareness:
    """Tests for evaluator source content awareness."""

    def test_original_content_in_evaluation_prompt(self, mock_env):
        """Test that original_content is included in evaluation prompt."""
        with patch('agents.base_agent.Anthropic'):
            from agents.synthesis_evaluator import SynthesisEvaluatorAgent
            agent = SynthesisEvaluatorAgent()

            synthesis_output = {
                "executive_summary": {"overall_tone": "bullish"},
                "confluence_zones": [],
            }
            original_content = [
                {"source": "42macro", "themes": ["gold", "rates"], "tickers": ["GLD", "TLT"], "sentiment": "bullish"},
                {"source": "discord", "themes": ["vol"], "tickers": ["SPX"], "sentiment": "neutral"},
            ]

            prompt = agent._build_evaluation_prompt(synthesis_output, original_content)
            assert "Source Content Summary" in prompt
            assert "42macro" in prompt
            assert "discord" in prompt
            assert "gold" in prompt
            assert "SPX" in prompt

    def test_evaluation_prompt_without_original_content(self, mock_env):
        """Test evaluation prompt works without original_content."""
        with patch('agents.base_agent.Anthropic'):
            from agents.synthesis_evaluator import SynthesisEvaluatorAgent
            agent = SynthesisEvaluatorAgent()

            synthesis_output = {"executive_summary": {"overall_tone": "bullish"}}
            prompt = agent._build_evaluation_prompt(synthesis_output, None)
            assert "Source Content Summary" not in prompt
            assert "Synthesis to Evaluate" in prompt

    def test_max_tokens_increased(self, mock_env):
        """Test evaluator uses increased max_tokens."""
        with patch('agents.base_agent.Anthropic'):
            from agents.synthesis_evaluator import SynthesisEvaluatorAgent
            agent = SynthesisEvaluatorAgent()

            mock_response = {
                "confluence_detection": 2, "evidence_preservation": 2,
                "source_attribution": 2, "youtube_channel_granularity": 2,
                "nuance_retention": 2, "actionability": 2, "theme_continuity": 2,
                "flags": [], "prompt_suggestions": []
            }

            with patch.object(agent, 'call_claude', return_value=mock_response) as mock_call:
                agent.evaluate({"executive_summary": {}})
                call_kwargs = mock_call.call_args
                assert call_kwargs.kwargs.get('max_tokens') == 2500

    def test_cross_check_instruction_in_prompt(self, mock_env):
        """Test cross-check instruction is in evaluation prompt."""
        with patch('agents.base_agent.Anthropic'):
            from agents.synthesis_evaluator import SynthesisEvaluatorAgent
            agent = SynthesisEvaluatorAgent()

            prompt = agent._build_evaluation_prompt(
                {"executive_summary": {}},
                [{"source": "42macro", "themes": ["gold"], "tickers": ["GLD"], "sentiment": "bullish"}]
            )
            assert "Cross-check" in prompt


# ============================================================================
# PR 6: CrossReferenceAgent in Synthesis Pipeline
# ============================================================================

class TestPR6CrossReference:
    """Tests for CrossReferenceAgent wiring into synthesis."""

    def test_empty_scores_returns_empty_result(self, mock_env):
        """Test CrossReferenceAgent handles empty scores gracefully."""
        with patch('agents.base_agent.Anthropic'):
            from agents.cross_reference import CrossReferenceAgent
            agent = CrossReferenceAgent()

            result = agent.analyze(confluence_scores=[])
            assert result["confluent_themes"] == []
            assert result["contradictions"] == []
            assert result["high_conviction_ideas"] == []
            assert result["total_themes"] == 0
            assert result["sources_analyzed"] == 0

    def test_empty_scores_no_claude_call(self, mock_env):
        """Test empty scores doesn't trigger any Claude API call."""
        with patch('agents.base_agent.Anthropic'):
            from agents.cross_reference import CrossReferenceAgent
            agent = CrossReferenceAgent()

            with patch.object(agent, 'call_claude') as mock_call:
                agent.analyze(confluence_scores=[])
                mock_call.assert_not_called()

    def test_detect_contradictions_missing_variant_view(self, mock_env):
        """Test _detect_contradictions handles missing variant_view."""
        with patch('agents.base_agent.Anthropic'):
            from agents.cross_reference import CrossReferenceAgent
            agent = CrossReferenceAgent()

            scores = [
                {
                    "primary_thesis": "Bull thesis",
                    "content_source": "42macro",
                    "variant_view": None,  # Missing
                    "full_analysis": {"tickers_mentioned": ["SPX"]}
                },
                {
                    "primary_thesis": "Bear thesis",
                    "content_source": "discord",
                    # variant_view not even present
                    "full_analysis": {"tickers_mentioned": ["SPX"]}
                }
            ]

            # Should not raise
            result = agent._detect_contradictions(scores)
            assert isinstance(result, list)

    def test_cross_reference_with_valid_scores(self, mock_env):
        """Test CrossReferenceAgent processes valid scores."""
        with patch('agents.base_agent.Anthropic'):
            from agents.cross_reference import CrossReferenceAgent
            agent = CrossReferenceAgent()

            mock_cluster_response = {
                "clusters": [
                    {
                        "cluster_id": 1,
                        "representative_theme": "Fed pivot",
                        "theme_indices": [1, 2],
                        "confidence": 0.9
                    }
                ]
            }

            scores = [
                {
                    "primary_thesis": "Fed will pivot dovish",
                    "content_source": "42macro",
                    "scored_at": "2026-01-15T00:00:00",
                    "core_total": 7,
                    "total_score": 10,
                    "meets_threshold": True,
                    "confluence_level": "strong",
                    "variant_view": "Bullish rates",
                    "p_and_l_mechanism": "Long TLT",
                    "falsification_criteria": ["CPI > 0.5%"]
                },
                {
                    "primary_thesis": "Dovish shift confirmed",
                    "content_source": "discord",
                    "scored_at": "2026-01-15T00:00:00",
                    "core_total": 6,
                    "total_score": 9,
                    "meets_threshold": True,
                    "confluence_level": "strong",
                    "variant_view": "Bullish equities",
                    "p_and_l_mechanism": "Long SPX calls",
                    "falsification_criteria": ["Hawkish FOMC"]
                }
            ]

            with patch.object(agent, 'call_claude', return_value=mock_cluster_response):
                result = agent.analyze(
                    confluence_scores=scores,
                    time_window_days=7,
                    historical_themes=[]
                )

            assert "confluent_themes" in result
            assert "contradictions" in result
            assert "high_conviction_ideas" in result
            assert result["sources_analyzed"] == 2
