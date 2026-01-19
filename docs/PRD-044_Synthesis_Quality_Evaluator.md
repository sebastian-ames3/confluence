# PRD-044: Macro Research Quality Evaluator

**Status**: Not Started
**Priority**: High
**Estimated Complexity**: Medium
**Target**: January 2026

## Overview

Create an automated quality evaluation agent that grades each synthesis output against domain-relevant criteria. This addresses the core user complaint of "over-summarization and missing nuance" by providing systematic quality feedback.

## Problem Statement

The system currently validates synthesis outputs for:
- Technical correctness (API returns 200)
- Schema validity (JSON well-formed)

But it lacks validation for:
- **Domain quality**: Is confluence correctly identified?
- **Nuance preservation**: Is important detail being lost?
- **Actionability**: Are there specific levels/triggers?
- **Quality regression**: Did a prompt change make output worse?

This means low-quality synthesis goes undetected until the user manually notices issues.

## Goals

1. Auto-grade synthesis on 7 domain-relevant criteria
2. Flag quality issues before user consumption
3. Track quality scores over time to detect regressions
4. Provide actionable feedback for prompt refinement

## Implementation Plan

### 44.1 Database Model

**File**: `backend/models.py`

**Model**: `SynthesisQualityScore`
```python
class SynthesisQualityScore(Base):
    __tablename__ = "synthesis_quality_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    synthesis_id = Column(Integer, ForeignKey("syntheses.id", ondelete="CASCADE"), nullable=False)

    # Overall score (0-100)
    quality_score = Column(Integer, nullable=False)
    grade = Column(String(2), nullable=False)  # A+, A, A-, B+, B, B-, C+, C, C-, D, F

    # Individual criterion scores (0-3 scale: 0=fail, 1=poor, 2=acceptable, 3=good)
    confluence_detection = Column(Integer, nullable=False)
    evidence_preservation = Column(Integer, nullable=False)
    source_attribution = Column(Integer, nullable=False)
    youtube_channel_granularity = Column(Integer, nullable=False)
    nuance_retention = Column(Integer, nullable=False)
    actionability = Column(Integer, nullable=False)
    theme_continuity = Column(Integer, nullable=False)

    # Detailed feedback
    flags = Column(JSON)  # Array of {criterion, score, detail}
    prompt_suggestions = Column(JSON)  # Array of improvement suggestions

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    synthesis = relationship("Synthesis", back_populates="quality_score")
```

### 44.2 Quality Evaluator Agent

**File**: `agents/synthesis_evaluator.py`

**SynthesisEvaluatorAgent**:
- Uses Claude Sonnet 4 (not Opus - cost-effective for evaluation)
- Takes synthesis output + original content as input
- Returns structured quality assessment

**Evaluation Criteria**:

| Criterion | Weight | What It Checks | Example Pass | Example Fail |
|-----------|--------|----------------|--------------|--------------|
| Confluence Detection | 20% | Are cross-source alignments identified? | "42Macro and KT both see SPX support at 5950" | "Sources are bullish" |
| Evidence Preservation | 15% | Do themes have supporting data points? | "KISS model at +1.2, above 0.5 threshold" | "42Macro is bullish" |
| Source Attribution | 15% | Can insights be traced to specific sources? | "Forward Guidance noted Fed pivot risk" | "YouTube discussed rates" |
| YouTube Channel Granularity | 15% | Are channels named individually (not generic "YouTube")? | "Moonshots covered AI workforce impact" | "YouTube mentioned AI" |
| Nuance Retention | 15% | Are conflicting views within sources captured? | "Bullish long-term but cautious near-term" | "Moonshots bullish" |
| Actionability | 10% | Are there specific levels, triggers, timeframes? | "Watch 5900 SPX - break below invalidates" | "Support is important" |
| Theme Continuity | 10% | Does it reference theme evolution over time? | "Gold thesis from Dec 15 now has 3 confirms" | No historical context |

**Grading Scale**:
- A+: 95-100, A: 90-94, A-: 85-89
- B+: 80-84, B: 75-79, B-: 70-74
- C+: 65-69, C: 60-64, C-: 55-59
- D: 50-54
- F: Below 50

**Agent Prompt** (system message):
```
You are a quality evaluator for investment research synthesis. Your job is to grade synthesis outputs against specific criteria that matter for research consumption.

You are NOT evaluating trade ideas - you are evaluating whether the synthesis accurately captures and preserves the insights from the source research.

Evaluate strictly. A score of 3 means the criterion is fully met. A score of 0 means it completely fails.
```

### 44.3 Integration with Synthesis Pipeline

**File**: `backend/routes/synthesis.py`

**Integration Point**: After successful synthesis generation in `generate_synthesis()`:
```python
# After synthesis is saved to database
if synthesis_id and os.getenv("ENABLE_QUALITY_EVALUATION", "true") == "true":
    try:
        evaluator = SynthesisEvaluatorAgent()
        quality_result = await evaluator.evaluate(
            synthesis_output=synthesis_response,
            original_content=content_items
        )
        # Save quality score
        quality_score = SynthesisQualityScore(
            synthesis_id=synthesis_id,
            **quality_result
        )
        db.add(quality_score)
        await db.commit()
    except Exception as e:
        logger.warning(f"Quality evaluation failed: {e}")
        # Don't fail the synthesis if evaluation fails
```

### 44.4 API Endpoints

**File**: `backend/routes/synthesis.py` (add endpoints)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/synthesis/{id}/quality` | GET | Get quality score for synthesis |
| `/api/synthesis/quality/trend` | GET | Get quality scores over time (last 30 days) |
| `/api/synthesis/quality/flags` | GET | Get all flagged quality issues |

### 44.5 Dashboard Widget

**File**: `frontend/index.html` (add to Overview tab)

**Quality Indicator**:
- Show grade badge next to synthesis timestamp (A+, B-, etc.)
- Color-coded: Green (A/B), Yellow (C), Red (D/F)
- Click to expand quality details

**Quality Details Panel**:
- Radar chart showing 7 criteria scores
- List of specific flags/issues
- Prompt improvement suggestions (collapsible)

**Trend Chart** (in a separate "Quality" section):
- Line chart of quality scores over last 30 syntheses
- Highlight regressions (score drop > 10 points)

### 44.6 MCP Tool

**File**: `mcp/server.py`

**Tool**: `get_synthesis_quality`
```python
@mcp_tool
def get_synthesis_quality(synthesis_id: Optional[int] = None):
    """
    Get quality evaluation for a synthesis.
    If no ID provided, returns quality for most recent synthesis.

    Returns:
    - quality_score: 0-100
    - grade: A+ through F
    - flags: List of quality issues
    - prompt_suggestions: How to improve
    """
```

## Success Criteria

1. Quality evaluator runs automatically after each synthesis generation
2. Quality scores are stored and retrievable via API
3. Dashboard shows quality grade and trend over time
4. Low scores (<70) are flagged visually
5. MCP tool allows querying quality from Claude Desktop
6. Token cost per evaluation is <1000 tokens

## Token Budget

- Evaluator input: ~2000 tokens (synthesis output + sample of original content)
- Evaluator output: ~500 tokens (structured quality assessment)
- Total per evaluation: ~2500 tokens (~$0.02 with Sonnet)

## Definition of Done

### Database Model
- [ ] `SynthesisQualityScore` model added to `backend/models.py`
- [ ] Model includes all 7 criterion score columns
- [ ] Model has `flags` and `prompt_suggestions` JSON columns
- [ ] Foreign key relationship to `syntheses` table with CASCADE delete
- [ ] Migration script runs without errors

### Quality Evaluator Agent
- [ ] `agents/synthesis_evaluator.py` file created
- [ ] `SynthesisEvaluatorAgent` class extends `BaseAgent`
- [ ] `evaluate()` method takes synthesis output + original content
- [ ] Returns structured dict with all 7 criterion scores
- [ ] Returns overall quality_score (0-100) and grade (A+ through F)
- [ ] Returns flags array with issues found
- [ ] Returns prompt_suggestions array
- [ ] Uses Claude Sonnet 4 (not Opus) for cost efficiency
- [ ] Handles API errors gracefully (retry logic from PRD-034)

### Pipeline Integration
- [ ] `backend/routes/synthesis.py` calls evaluator after synthesis generation
- [ ] Evaluation runs asynchronously (doesn't block synthesis return)
- [ ] Quality score saved to database
- [ ] Evaluation failures logged but don't fail synthesis
- [ ] `ENABLE_QUALITY_EVALUATION` env var controls feature

### API Endpoints
- [ ] `GET /api/synthesis/{id}/quality` returns quality score for specific synthesis
- [ ] `GET /api/synthesis/quality/trend` returns scores for last 30 days
- [ ] `GET /api/synthesis/quality/flags` returns all flagged issues
- [ ] All endpoints require authentication (JWT or Basic)
- [ ] All endpoints have proper error handling

### Dashboard UI
- [ ] Quality grade badge displayed next to synthesis timestamp
- [ ] Badge color-coded: Green (A/B), Yellow (C), Red (D/F)
- [ ] Click badge expands quality details panel
- [ ] Details panel shows radar chart of 7 criteria
- [ ] Details panel lists specific flags/issues
- [ ] Prompt suggestions shown in collapsible section
- [ ] Quality trend chart shows last 30 syntheses
- [ ] Regressions (>10 point drop) highlighted in red
- [ ] Mobile responsive

### MCP Tool
- [ ] `get_synthesis_quality` tool added to `mcp/server.py`
- [ ] Returns quality_score, grade, flags, prompt_suggestions
- [ ] Defaults to most recent synthesis if no ID provided

### Testing
- [ ] Unit tests pass (`tests/test_prd044_quality_evaluator.py`)
- [ ] Integration tests pass
- [ ] Playwright UI tests pass (`tests/playwright/prd044-quality.spec.js`)

### Documentation
- [ ] CLAUDE.md updated with quality evaluator info
- [ ] PRD moved to `/docs/archived/` on completion

---

## Testing Requirements

**Unit Tests** (`tests/test_prd044_quality_evaluator.py`):
- Test each criterion scoring logic
- Test grade calculation from criterion scores
- Test edge cases (empty synthesis, missing sections)
- Test flags generation for low scores
- Test prompt_suggestions generation
- Test model relationships and cascades

**Integration Tests**:
- Test end-to-end flow: synthesis → evaluation → storage
- Test API endpoints return correct data
- Test evaluation doesn't block synthesis return
- Test ENABLE_QUALITY_EVALUATION toggle works

**UI Tests** (`tests/playwright/prd044-quality.spec.js`):
- Quality badge renders next to synthesis timestamp
- Badge shows correct color based on grade
- Click badge expands details panel
- Radar chart renders with 7 axes
- Flags list displays correctly
- Prompt suggestions collapsible works
- Trend chart renders with data points
- Regression highlighting works
- Mobile responsive layout

## Dependencies

- PRD-038 (User Engagement) - UI patterns for feedback display
- Existing synthesis infrastructure

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Evaluator adds latency to synthesis | Run async; don't block synthesis return |
| False positives on quality flags | Tune prompts based on first 50 evaluations |
| Cost creep from evaluation | Use Sonnet (cheaper); cap at 1 eval per synthesis |
