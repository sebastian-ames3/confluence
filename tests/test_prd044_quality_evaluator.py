"""
Tests for PRD-044: Synthesis Quality Evaluator

Tests cover:
1. SynthesisQualityScore database model
2. SynthesisEvaluatorAgent
3. Quality API endpoints
4. Quality route logic
5. MCP tool integration
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_synthesis_v3():
    """Sample V3 synthesis output for testing."""
    return {
        "executive_summary": {
            "macro_context": "Markets are in a consolidation phase...",
            "synthesis_narrative": "42Macro and KT Technical both see SPX support at 5950...",
            "key_takeaways": [
                "KISS model at +1.2, above 0.5 threshold per 42Macro",
                "Forward Guidance noted Fed pivot risk on Jan 15"
            ],
            "overall_tone": "cautious"
        },
        "confluence_zones": [
            {
                "theme": "SPX Support",
                "confluence_strength": 85,
                "sources_aligned": ["42Macro", "KT Technical"],
                "view": "5950 level is key support"
            }
        ],
        "source_stances": {
            "42macro": {
                "narrative": "KISS model positive, tactically constructive",
                "key_themes": ["Liquidity", "Positioning"],
                "bias": "cautiously_bullish"
            },
            "moonshots": {
                "narrative": "Bullish long-term but cautious near-term due to positioning",
                "key_themes": ["AI Infrastructure"],
                "bias": "mixed"
            }
        },
        "conflict_watch": [
            {
                "topic": "Rate path",
                "bull_case": {"view": "Cuts coming Q1", "sources": ["Forward Guidance"]},
                "bear_case": {"view": "Inflation sticky", "sources": ["42Macro"]}
            }
        ],
        "attention_priorities": [
            {
                "rank": 1,
                "focus": "SPX 5900 level",
                "why_it_matters": "Break below invalidates bullish thesis per KT",
                "time_sensitivity": "immediate"
            }
        ],
        "catalyst_calendar": [
            {
                "date": "2025-01-20",
                "event": "FOMC Minutes",
                "impact": "high"
            }
        ],
        "sources_included": ["42macro", "kt_technical", "youtube"],
        "content_count": 15
    }


@pytest.fixture
def mock_quality_result():
    """Sample quality evaluation result."""
    return {
        "quality_score": 78,
        "grade": "B+",
        "confluence_detection": 3,
        "evidence_preservation": 2,
        "source_attribution": 3,
        "youtube_channel_granularity": 2,
        "nuance_retention": 2,
        "actionability": 2,
        "theme_continuity": 1,
        "flags": [
            {
                "criterion": "Theme Continuity",
                "score": 1,
                "detail": "No historical context for themes"
            }
        ],
        "prompt_suggestions": [
            "Add references to how themes have evolved from previous syntheses"
        ]
    }


# ============================================================================
# Model Tests
# ============================================================================

class TestSynthesisQualityScoreModel:
    """Tests for the SynthesisQualityScore ORM model."""

    def test_model_exists(self):
        """Model can be imported."""
        from backend.models import SynthesisQualityScore
        assert SynthesisQualityScore is not None

    def test_model_tablename(self):
        """Model has correct table name."""
        from backend.models import SynthesisQualityScore
        assert SynthesisQualityScore.__tablename__ == "synthesis_quality_scores"

    def test_model_columns(self):
        """Model has all required columns."""
        from backend.models import SynthesisQualityScore

        required_columns = [
            'id', 'synthesis_id', 'quality_score', 'grade',
            'confluence_detection', 'evidence_preservation',
            'source_attribution', 'youtube_channel_granularity',
            'nuance_retention', 'actionability', 'theme_continuity',
            'flags', 'prompt_suggestions', 'created_at'
        ]

        actual_columns = [c.name for c in SynthesisQualityScore.__table__.columns]
        for col in required_columns:
            assert col in actual_columns, f"Missing column: {col}"

    def test_model_relationship(self):
        """Model has relationship to Synthesis."""
        from backend.models import SynthesisQualityScore
        from sqlalchemy.orm import RelationshipProperty

        # Check that synthesis relationship exists
        assert hasattr(SynthesisQualityScore, 'synthesis')


# ============================================================================
# Evaluator Agent Tests
# ============================================================================

class TestSynthesisEvaluatorAgent:
    """Tests for SynthesisEvaluatorAgent."""

    def test_agent_can_be_imported(self):
        """Agent can be imported."""
        from agents.synthesis_evaluator import SynthesisEvaluatorAgent
        assert SynthesisEvaluatorAgent is not None

    def test_agent_uses_sonnet_model(self):
        """Agent uses Sonnet for cost efficiency."""
        from agents.synthesis_evaluator import SynthesisEvaluatorAgent

        with patch.dict('os.environ', {'CLAUDE_API_KEY': 'test-key'}):
            agent = SynthesisEvaluatorAgent()
            assert 'sonnet' in agent.model.lower()

    def test_criterion_weights_sum_to_100(self):
        """Criterion weights should sum to 100%."""
        from agents.synthesis_evaluator import CRITERION_WEIGHTS

        total = sum(CRITERION_WEIGHTS.values())
        assert total == pytest.approx(1.0, abs=0.01), f"Weights sum to {total}, expected 1.0"

    def test_grade_calculation(self):
        """Grade calculation works correctly."""
        from agents.synthesis_evaluator import calculate_grade

        assert calculate_grade(95) == "A+"
        assert calculate_grade(90) == "A"
        assert calculate_grade(85) == "A-"
        assert calculate_grade(80) == "B+"
        assert calculate_grade(75) == "B"
        assert calculate_grade(70) == "B-"
        assert calculate_grade(65) == "C+"
        assert calculate_grade(60) == "C"
        assert calculate_grade(55) == "C-"
        assert calculate_grade(50) == "D"
        assert calculate_grade(40) == "F"
        assert calculate_grade(0) == "F"

    def test_overall_score_calculation(self):
        """Overall score calculation from criterion scores."""
        from agents.synthesis_evaluator import calculate_overall_score

        # Perfect scores should give 100
        perfect_scores = {
            "confluence_detection": 3,
            "evidence_preservation": 3,
            "source_attribution": 3,
            "youtube_channel_granularity": 3,
            "nuance_retention": 3,
            "actionability": 3,
            "theme_continuity": 3
        }
        assert calculate_overall_score(perfect_scores) == 100

        # Zero scores should give 0
        zero_scores = {k: 0 for k in perfect_scores.keys()}
        assert calculate_overall_score(zero_scores) == 0

        # Mixed scores
        mixed_scores = {
            "confluence_detection": 2,  # 20% weight, 2/3 = 67% -> 13.3 points
            "evidence_preservation": 3,  # 15% weight, 3/3 = 100% -> 15 points
            "source_attribution": 2,  # 15% weight, 2/3 = 67% -> 10 points
            "youtube_channel_granularity": 1,  # 15% weight, 1/3 = 33% -> 5 points
            "nuance_retention": 2,  # 15% weight, 2/3 = 67% -> 10 points
            "actionability": 3,  # 10% weight, 3/3 = 100% -> 10 points
            "theme_continuity": 1  # 10% weight, 1/3 = 33% -> 3.3 points
        }
        score = calculate_overall_score(mixed_scores)
        assert 60 <= score <= 70  # Should be around 67

    @patch('agents.base_agent.Anthropic')
    def test_evaluate_returns_expected_structure(self, mock_anthropic, mock_synthesis_v3):
        """Evaluate method returns correctly structured result."""
        from agents.synthesis_evaluator import SynthesisEvaluatorAgent

        # Mock Claude response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "confluence_detection": 3,
            "evidence_preservation": 2,
            "source_attribution": 3,
            "youtube_channel_granularity": 2,
            "nuance_retention": 2,
            "actionability": 2,
            "theme_continuity": 1,
            "flags": [],
            "prompt_suggestions": []
        }))]
        mock_anthropic.return_value.messages.create.return_value = mock_response

        with patch.dict('os.environ', {'CLAUDE_API_KEY': 'test-key'}):
            agent = SynthesisEvaluatorAgent()
            result = agent.evaluate(mock_synthesis_v3)

        # Check required keys
        assert "quality_score" in result
        assert "grade" in result
        assert "confluence_detection" in result
        assert "evidence_preservation" in result
        assert "flags" in result
        assert "prompt_suggestions" in result

        # Check score ranges
        assert 0 <= result["quality_score"] <= 100
        assert result["grade"] in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]

    def test_error_result_generation(self):
        """Error result is properly formatted."""
        from agents.synthesis_evaluator import SynthesisEvaluatorAgent

        with patch.dict('os.environ', {'CLAUDE_API_KEY': 'test-key'}):
            agent = SynthesisEvaluatorAgent()
            result = agent._generate_error_result("Test error")

        assert result["quality_score"] == 0
        assert result["grade"] == "F"
        assert len(result["flags"]) == 1
        assert "Test error" in result["flags"][0]["detail"]


# ============================================================================
# API Route Tests
# ============================================================================

class TestQualityRoutes:
    """Tests for quality API routes."""

    def test_quality_routes_importable(self):
        """Quality routes module can be imported."""
        from backend.routes import quality
        assert quality.router is not None

    def test_format_quality_response(self):
        """Helper function formats response correctly."""
        from backend.routes.quality import _format_quality_response
        from unittest.mock import MagicMock

        # Create mock quality score object
        mock_quality = MagicMock()
        mock_quality.synthesis_id = 1
        mock_quality.quality_score = 78
        mock_quality.grade = "B+"
        mock_quality.confluence_detection = 3
        mock_quality.evidence_preservation = 2
        mock_quality.source_attribution = 3
        mock_quality.youtube_channel_granularity = 2
        mock_quality.nuance_retention = 2
        mock_quality.actionability = 2
        mock_quality.theme_continuity = 1
        mock_quality.flags = json.dumps([{"criterion": "Test", "score": 1, "detail": "Test issue"}])
        mock_quality.prompt_suggestions = json.dumps(["Test suggestion"])
        mock_quality.created_at = datetime(2025, 1, 15, 12, 0, 0)

        result = _format_quality_response(mock_quality)

        assert result["synthesis_id"] == 1
        assert result["quality_score"] == 78
        assert result["grade"] == "B+"
        assert "criterion_scores" in result
        assert result["criterion_scores"]["confluence_detection"] == 3
        assert len(result["flags"]) == 1
        assert len(result["prompt_suggestions"]) == 1

    def test_flag_severity_calculation(self):
        """Flag severity is calculated correctly."""
        from backend.routes.quality import _get_flag_severity

        assert _get_flag_severity(0) == "high"
        assert _get_flag_severity(1) == "medium"
        assert _get_flag_severity(2) == "low"
        assert _get_flag_severity(3) == "low"


# ============================================================================
# Integration Tests
# ============================================================================

class TestSynthesisPipelineIntegration:
    """Tests for quality evaluation integration in synthesis pipeline."""

    def test_synthesis_routes_import_quality_components(self):
        """Synthesis routes import quality components."""
        from backend.routes import synthesis

        # Check imports are present
        source_code = open('backend/routes/synthesis.py', encoding='utf-8').read()
        assert 'SynthesisQualityScore' in source_code
        assert 'SynthesisEvaluatorAgent' in source_code

    def test_quality_evaluation_is_optional(self):
        """Quality evaluation can be disabled via env var."""
        source_code = open('backend/routes/synthesis.py', encoding='utf-8').read()
        assert 'ENABLE_QUALITY_EVALUATION' in source_code


# ============================================================================
# MCP Tool Tests
# ============================================================================

class TestMCPQualityTool:
    """Tests for MCP get_synthesis_quality tool."""

    def test_confluence_client_has_quality_method(self):
        """ConfluenceClient has get_synthesis_quality method."""
        # Use file-based check to avoid MCP dependency issues in test env
        content = open('mcp/confluence_client.py', encoding='utf-8').read()
        assert 'def get_synthesis_quality' in content
        assert 'get_quality_trends' in content

    def test_mcp_server_has_quality_tool(self):
        """MCP server includes quality tool."""
        source_code = open('mcp/server.py', encoding='utf-8').read()
        assert 'get_synthesis_quality' in source_code

    def test_quality_tool_definition(self):
        """Quality tool has proper definition."""
        source_code = open('mcp/server.py', encoding='utf-8').read()

        # Check tool name is defined
        assert 'name="get_synthesis_quality"' in source_code

        # Check description mentions key features
        assert 'quality' in source_code.lower()
        assert 'grade' in source_code.lower()


# ============================================================================
# Frontend Tests (existence checks)
# ============================================================================

class TestFrontendQualityComponents:
    """Tests for frontend quality components."""

    def test_quality_js_exists(self):
        """quality.js file exists."""
        from pathlib import Path
        js_path = Path('frontend/js/quality.js')
        assert js_path.exists(), "frontend/js/quality.js not found"

    def test_quality_css_exists(self):
        """quality CSS file exists."""
        from pathlib import Path
        css_path = Path('frontend/css/components/_quality.css')
        assert css_path.exists(), "frontend/css/components/_quality.css not found"

    def test_quality_js_has_required_functions(self):
        """quality.js has required functions."""
        content = open('frontend/js/quality.js', encoding='utf-8').read()

        assert 'QualityManager' in content
        assert 'loadLatestQuality' in content
        assert 'renderQualityWidget' in content
        assert 'getGradeClass' in content

    def test_quality_css_has_required_styles(self):
        """quality CSS has required styles."""
        content = open('frontend/css/components/_quality.css', encoding='utf-8').read()

        assert '.quality-widget' in content
        assert '.quality-grade' in content
        assert '.criterion-bar' in content
        assert '.grade-a' in content
        assert '.grade-f' in content

    def test_quality_js_included_in_index(self):
        """quality.js is included in index.html."""
        content = open('frontend/index.html', encoding='utf-8').read()
        assert 'quality.js' in content

    def test_quality_css_imported_in_components(self):
        """quality CSS is imported in components.css."""
        content = open('frontend/css/components/components.css', encoding='utf-8').read()
        assert '_quality.css' in content


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_synthesis_handling(self):
        """Evaluator handles empty synthesis gracefully."""
        from agents.synthesis_evaluator import SynthesisEvaluatorAgent

        with patch.dict('os.environ', {'CLAUDE_API_KEY': 'test-key'}):
            agent = SynthesisEvaluatorAgent()

            # Should not raise, should return error result
            with patch.object(agent, 'call_claude', side_effect=Exception("Empty input")):
                result = agent.evaluate({})

            assert result["quality_score"] == 0
            assert result["grade"] == "F"

    def test_malformed_criterion_scores(self):
        """Score calculation handles malformed inputs."""
        from agents.synthesis_evaluator import calculate_overall_score

        # Missing criteria should use 0
        partial_scores = {
            "confluence_detection": 3,
            "evidence_preservation": 3
            # Missing other criteria
        }
        score = calculate_overall_score(partial_scores)
        assert 0 <= score <= 100

    def test_grade_boundary_conditions(self):
        """Grade boundaries are handled correctly."""
        from agents.synthesis_evaluator import calculate_grade

        # Test exact boundaries
        assert calculate_grade(95) == "A+"
        assert calculate_grade(94) == "A"
        assert calculate_grade(90) == "A"
        assert calculate_grade(89) == "A-"
        assert calculate_grade(85) == "A-"
        assert calculate_grade(84) == "B+"

    def test_json_flags_parsing(self):
        """JSON flags are parsed correctly in responses."""
        from backend.routes.quality import _format_quality_response
        from unittest.mock import MagicMock

        mock_quality = MagicMock()
        mock_quality.synthesis_id = 1
        mock_quality.quality_score = 50
        mock_quality.grade = "D"
        mock_quality.confluence_detection = 1
        mock_quality.evidence_preservation = 1
        mock_quality.source_attribution = 1
        mock_quality.youtube_channel_granularity = 1
        mock_quality.nuance_retention = 1
        mock_quality.actionability = 1
        mock_quality.theme_continuity = 1
        mock_quality.flags = "invalid json"  # Invalid JSON
        mock_quality.prompt_suggestions = None
        mock_quality.created_at = datetime.utcnow()

        # Should not raise, should return empty list for invalid JSON
        result = _format_quality_response(mock_quality)
        assert result["flags"] == []
        assert result["prompt_suggestions"] == []


# ============================================================================
# Performance and Resource Tests
# ============================================================================

class TestPerformance:
    """Tests for performance and resource usage."""

    def test_evaluation_prompt_length(self):
        """Evaluation prompt stays within reasonable token limits."""
        from agents.synthesis_evaluator import SynthesisEvaluatorAgent

        with patch.dict('os.environ', {'CLAUDE_API_KEY': 'test-key'}):
            agent = SynthesisEvaluatorAgent()

            # Create a large synthesis
            large_synthesis = {
                "executive_summary": {"narrative": "x" * 5000},
                "confluence_zones": [{"theme": f"theme_{i}"} for i in range(50)],
                "source_stances": {f"source_{i}": {"narrative": "x" * 500} for i in range(10)}
            }

            prompt = agent._build_evaluation_prompt(large_synthesis)

            # Prompt should be truncated
            assert len(prompt) < 15000  # Reasonable limit for API call

    def test_criterion_weight_coverage(self):
        """All criteria have defined weights."""
        from agents.synthesis_evaluator import CRITERION_WEIGHTS

        expected_criteria = [
            "confluence_detection",
            "evidence_preservation",
            "source_attribution",
            "youtube_channel_granularity",
            "nuance_retention",
            "actionability",
            "theme_continuity"
        ]

        for criterion in expected_criteria:
            assert criterion in CRITERION_WEIGHTS, f"Missing weight for {criterion}"
            assert 0 < CRITERION_WEIGHTS[criterion] <= 1, f"Invalid weight for {criterion}"
