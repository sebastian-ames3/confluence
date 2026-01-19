"""
Synthesis Quality Evaluator Agent (PRD-044)

Evaluates synthesis outputs against 7 domain-relevant criteria:
1. Confluence Detection - Cross-source alignments identified
2. Evidence Preservation - Themes have supporting data points
3. Source Attribution - Insights traced to specific sources
4. YouTube Channel Granularity - Channels named individually
5. Nuance Retention - Conflicting views captured
6. Actionability - Specific levels, triggers, timeframes
7. Theme Continuity - References theme evolution over time

Uses Claude Sonnet for cost-effective evaluation (~$0.02 per evaluation).
"""

import logging
import json
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


# Criterion weights for overall score calculation
CRITERION_WEIGHTS = {
    "confluence_detection": 0.20,      # 20%
    "evidence_preservation": 0.15,     # 15%
    "source_attribution": 0.15,        # 15%
    "youtube_channel_granularity": 0.15,  # 15%
    "nuance_retention": 0.15,          # 15%
    "actionability": 0.10,             # 10%
    "theme_continuity": 0.10           # 10%
}

# Grading scale
GRADE_THRESHOLDS = [
    (95, "A+"),
    (90, "A"),
    (85, "A-"),
    (80, "B+"),
    (75, "B"),
    (70, "B-"),
    (65, "C+"),
    (60, "C"),
    (55, "C-"),
    (50, "D"),
    (0, "F")
]


def calculate_grade(score: int) -> str:
    """Convert numeric score (0-100) to letter grade."""
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"


def calculate_overall_score(criterion_scores: Dict[str, int]) -> int:
    """
    Calculate weighted overall score from criterion scores.

    Args:
        criterion_scores: Dict of criterion name to score (0-3)

    Returns:
        Overall score 0-100
    """
    weighted_sum = 0
    for criterion, weight in CRITERION_WEIGHTS.items():
        score = criterion_scores.get(criterion, 0)
        # Convert 0-3 scale to 0-100 scale (0=0, 1=33, 2=67, 3=100)
        normalized = (score / 3) * 100
        weighted_sum += normalized * weight

    return round(weighted_sum)


class SynthesisEvaluatorAgent(BaseAgent):
    """
    Evaluates synthesis quality against domain-relevant criteria.

    Uses Claude Sonnet (not Opus) for cost efficiency.
    Returns structured quality assessment with scores, flags, and suggestions.
    """

    SYSTEM_PROMPT = """You are a quality evaluator for investment research synthesis. Your job is to grade synthesis outputs against specific criteria that matter for research consumption.

You are NOT evaluating trade ideas - you are evaluating whether the synthesis accurately captures and preserves the insights from the source research.

## Scoring Scale (0-3)
- 3 = Excellent: Criterion fully met with high quality
- 2 = Acceptable: Criterion met but could be better
- 1 = Poor: Criterion partially met with significant gaps
- 0 = Fail: Criterion not met at all

Evaluate strictly. A score of 3 means the criterion is fully met. A score of 0 means it completely fails.

## Response Format
Return a JSON object with this exact structure:
{
    "confluence_detection": <0-3>,
    "evidence_preservation": <0-3>,
    "source_attribution": <0-3>,
    "youtube_channel_granularity": <0-3>,
    "nuance_retention": <0-3>,
    "actionability": <0-3>,
    "theme_continuity": <0-3>,
    "flags": [
        {
            "criterion": "<criterion_name>",
            "score": <0-3>,
            "detail": "<specific issue description>"
        }
    ],
    "prompt_suggestions": [
        "<specific suggestion for improving the synthesis prompt>"
    ]
}

Only include entries in "flags" for criteria with scores of 1 or lower.
Include 1-3 prompt_suggestions based on the most significant issues found."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Synthesis Evaluator Agent.

        Uses Sonnet model for cost efficiency.
        """
        # Use Sonnet for cost-effective evaluation
        super().__init__(api_key=api_key, model="claude-sonnet-4-20250514")

    def evaluate(
        self,
        synthesis_output: Dict[str, Any],
        original_content: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a synthesis output against quality criteria.

        Args:
            synthesis_output: The generated synthesis (full JSON response)
            original_content: Optional list of source content items (for reference)

        Returns:
            Dict with:
                - quality_score: 0-100
                - grade: A+ through F
                - confluence_detection, evidence_preservation, etc.: 0-3 each
                - flags: List of {criterion, score, detail}
                - prompt_suggestions: List of improvement suggestions
        """
        try:
            # Build evaluation prompt
            prompt = self._build_evaluation_prompt(synthesis_output, original_content)

            # Call Claude for evaluation
            response = self.call_claude(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                max_tokens=1500,
                temperature=0.0,
                expect_json=True
            )

            # Validate required criterion scores
            required_criteria = list(CRITERION_WEIGHTS.keys())
            for criterion in required_criteria:
                if criterion not in response:
                    logger.warning(f"Missing criterion in evaluation: {criterion}")
                    response[criterion] = 1  # Default to poor if missing

                # Clamp scores to valid range
                response[criterion] = max(0, min(3, int(response[criterion])))

            # Calculate overall score and grade
            criterion_scores = {k: response[k] for k in required_criteria}
            overall_score = calculate_overall_score(criterion_scores)
            grade = calculate_grade(overall_score)

            # Ensure flags and suggestions are present
            if "flags" not in response or not isinstance(response["flags"], list):
                response["flags"] = self._generate_default_flags(criterion_scores)

            if "prompt_suggestions" not in response or not isinstance(response["prompt_suggestions"], list):
                response["prompt_suggestions"] = []

            # Build final result
            result = {
                "quality_score": overall_score,
                "grade": grade,
                **criterion_scores,
                "flags": response["flags"],
                "prompt_suggestions": response["prompt_suggestions"]
            }

            logger.info(f"Synthesis evaluation complete: {grade} ({overall_score}/100)")
            return result

        except Exception as e:
            logger.error(f"Synthesis evaluation failed: {e}")
            # Return a default "unable to evaluate" result
            return self._generate_error_result(str(e))

    def _build_evaluation_prompt(
        self,
        synthesis_output: Dict[str, Any],
        original_content: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Build the evaluation prompt from synthesis output.

        Args:
            synthesis_output: The synthesis JSON to evaluate
            original_content: Optional source content for reference

        Returns:
            Formatted prompt string
        """
        # Format synthesis for evaluation
        synthesis_str = json.dumps(synthesis_output, indent=2)

        # Truncate if too long (keep token budget reasonable)
        if len(synthesis_str) > 8000:
            synthesis_str = synthesis_str[:8000] + "\n... [truncated]"

        prompt = f"""## Synthesis to Evaluate

<synthesis>
{synthesis_str}
</synthesis>

## Evaluation Criteria

Evaluate the synthesis against these 7 criteria:

### 1. Confluence Detection (20% weight)
Are cross-source alignments explicitly identified?
- GOOD: "42Macro and KT Technical both see SPX support at 5950"
- BAD: "Sources are bullish" (no specific alignment)

### 2. Evidence Preservation (15% weight)
Do themes have supporting data points from the research?
- GOOD: "KISS model at +1.2, above 0.5 threshold per 42Macro"
- BAD: "42Macro is bullish" (no specific data)

### 3. Source Attribution (15% weight)
Can insights be traced to specific sources?
- GOOD: "Forward Guidance noted Fed pivot risk on Jan 15"
- BAD: "YouTube discussed rates" (generic, which channel?)

### 4. YouTube Channel Granularity (15% weight)
Are YouTube channels named individually, not as generic "YouTube"?
- GOOD: "Moonshots covered AI workforce impact on earnings"
- BAD: "YouTube mentioned AI trends" (which channel?)

### 5. Nuance Retention (15% weight)
Are conflicting views within sources captured?
- GOOD: "Moonshots is bullish long-term but cautious near-term due to positioning"
- BAD: "Moonshots is bullish" (missing the nuance)

### 6. Actionability (10% weight)
Are there specific levels, triggers, or timeframes?
- GOOD: "Watch 5900 SPX - break below invalidates bullish thesis per KT"
- BAD: "Support is important" (no specific level)

### 7. Theme Continuity (10% weight)
Does synthesis reference theme evolution over time?
- GOOD: "Gold thesis from Dec 15 now has 3 confirmations"
- BAD: No historical context for themes

## Instructions

1. Score each criterion 0-3
2. For any score of 1 or lower, add an entry to "flags" with specific details
3. Provide 1-3 actionable prompt_suggestions to improve future synthesis quality

Return your evaluation as a JSON object."""

        return prompt

    def _generate_default_flags(self, criterion_scores: Dict[str, int]) -> List[Dict[str, Any]]:
        """Generate flags for low-scoring criteria."""
        flags = []
        criterion_names = {
            "confluence_detection": "Confluence Detection",
            "evidence_preservation": "Evidence Preservation",
            "source_attribution": "Source Attribution",
            "youtube_channel_granularity": "YouTube Channel Granularity",
            "nuance_retention": "Nuance Retention",
            "actionability": "Actionability",
            "theme_continuity": "Theme Continuity"
        }

        for criterion, score in criterion_scores.items():
            if score <= 1:
                flags.append({
                    "criterion": criterion_names.get(criterion, criterion),
                    "score": score,
                    "detail": f"Score of {score}/3 indicates this criterion needs improvement"
                })

        return flags

    def _generate_error_result(self, error_message: str) -> Dict[str, Any]:
        """Generate a result when evaluation fails."""
        return {
            "quality_score": 0,
            "grade": "F",
            "confluence_detection": 0,
            "evidence_preservation": 0,
            "source_attribution": 0,
            "youtube_channel_granularity": 0,
            "nuance_retention": 0,
            "actionability": 0,
            "theme_continuity": 0,
            "flags": [{
                "criterion": "Evaluation Error",
                "score": 0,
                "detail": f"Evaluation failed: {error_message}"
            }],
            "prompt_suggestions": []
        }

    def analyze(self, *args, **kwargs) -> Dict[str, Any]:
        """Alias for evaluate() to match BaseAgent interface."""
        return self.evaluate(*args, **kwargs)
