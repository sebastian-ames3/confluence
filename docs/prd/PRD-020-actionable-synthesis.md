# PRD-020: Actionable Synthesis Enhancement

## Overview
Transform the synthesis agent output from a "theme summary" into an "actionable trading brief" that provides specific levels, quantified conviction, entry/exit criteria, and time-horizon bucketing for professional investment decision-making.

## Problem Statement
The current synthesis output provides useful thematic summaries but lacks the specificity required for actionable trading decisions:

**Current Output Limitations:**
- "VIX calendar spreads" → No strikes, expiries, or entry levels
- "SPX support levels" → No specific price numbers
- "High conviction" → No quantification (how many sources? what weighting?)
- No entry/stop/target framework
- No time horizon differentiation (tactical vs strategic)
- Contradictions identified but not resolved with a weighted view
- No catalyst calendar with specific dates

**User Impact:**
A sophisticated investor receiving current output must do significant additional work to translate themes into trades. The synthesis tells you *what people are talking about* but not *what to do*.

## Goals
1. Extract specific levels, strikes, and price targets from source content
2. Quantify conviction scoring (X/Y sources, with quality weighting)
3. Provide entry/stop/target framework for each high-conviction idea
4. Bucket ideas by time horizon (tactical: days/weeks, strategic: months)
5. Resolve contradictions with weighted synthesis view
6. Generate catalyst calendar with specific dates and impact ratings
7. Maintain current cost efficiency (~$0.04-0.06 per synthesis)

## Non-Goals
- Position sizing recommendations (legal/compliance concerns)
- Specific trade execution instructions
- Real-time price feeds or live data
- Backtesting or performance tracking
- Portfolio allocation percentages

## Output Schema Enhancement

### Current Schema
```json
{
  "synthesis": "string (1-3 paragraphs)",
  "key_themes": ["theme1", "theme2"],
  "high_conviction_ideas": [
    {
      "idea": "string",
      "sources": ["source1"],
      "confidence": "high|medium|low",
      "rationale": "string"
    }
  ],
  "contradictions": [...],
  "market_regime": "string",
  "catalysts": ["event1", "event2"]
}
```

### Enhanced Schema
```json
{
  "market_regime": {
    "current": "risk-on|risk-off|transitioning|range-bound",
    "direction": "improving|deteriorating|stable",
    "confidence": 0.0-1.0,
    "key_drivers": ["driver1", "driver2"]
  },

  "synthesis_summary": "string (2-3 sentences, executive summary)",

  "tactical_ideas": [
    {
      "idea": "string",
      "conviction_score": {
        "raw": "4/5",
        "weighted": 0.85,
        "sources_agreeing": ["source1", "source2"],
        "sources_disagreeing": ["source3"]
      },
      "trade_structure": {
        "instrument": "VIX|SPX|specific ticker",
        "direction": "long|short|spread",
        "structure": "calendar spread|butterfly|outright|etc",
        "entry_level": "specific number or range",
        "stop_level": "specific number",
        "target_level": "specific number or range"
      },
      "time_horizon": "1-3 days|1-2 weeks|2-4 weeks",
      "catalyst": "specific event driving the thesis",
      "invalidation": "what would make this thesis wrong",
      "rationale": "2-3 sentences explaining the thesis"
    }
  ],

  "strategic_ideas": [
    {
      "idea": "string",
      "conviction_score": {...},
      "thesis": "longer description of the macro thesis",
      "key_levels": {
        "support": ["level1", "level2"],
        "resistance": ["level1", "level2"]
      },
      "time_horizon": "1-3 months|3-6 months|6+ months",
      "triggers": ["what would cause acceleration"],
      "risks": ["what could derail this"]
    }
  ],

  "watch_list": [
    {
      "topic": "string",
      "status": "conflicting|developing|monitoring",
      "bull_case": {
        "view": "string",
        "sources": ["source1"]
      },
      "bear_case": {
        "view": "string",
        "sources": ["source2"]
      },
      "resolution_trigger": "what would resolve the conflict",
      "action": "wait for X before positioning"
    }
  ],

  "catalyst_calendar": [
    {
      "date": "2025-12-11",
      "event": "CPI Release",
      "impact": "high|medium|low",
      "relevance": "which ideas this affects",
      "consensus": "what market expects",
      "risk": "upside or downside surprise scenario"
    }
  ],

  "source_summary": {
    "sources_analyzed": 5,
    "content_items": 152,
    "by_source": {
      "42macro": {"items": 5, "weight": "high", "current_stance": "summary"},
      "discord": {"items": 77, "weight": "high", "current_stance": "summary"},
      ...
    }
  },

  "generated_at": "ISO timestamp",
  "time_window": "7d",
  "version": "2.0"
}
```

## Implementation

### Phase 1: Enhanced Prompt Engineering

#### 1. Update System Prompt

```python
# In agents/synthesis_agent.py

SYSTEM_PROMPT_V2 = """You are a senior macro strategist synthesizing investment research for a professional trading desk.

Your output must be ACTIONABLE, not merely observational. Every idea should include:
- Specific price levels (not "support levels" but "5950-5980 support zone")
- Quantified conviction (count sources agreeing/disagreeing)
- Clear entry, stop, and target levels where available in source material
- Time horizon classification (tactical: <4 weeks, strategic: 1-6 months)

SOURCE WEIGHTING (apply these weights when counting conviction):
- 42Macro (Darius Dale): 1.5x weight - institutional-grade macro research
- Discord Options Insight (Imran): 1.5x weight - professional options flow analysis
- KT Technical: 1.2x weight - systematic technical analysis
- Substack (Visser Labs): 1.0x weight - macro/crypto analysis
- YouTube: 0.8x weight - variable quality, verify with other sources

CONVICTION SCORING:
- Calculate raw score as (agreeing sources / total sources mentioning topic)
- Apply source weights to get weighted score
- High conviction: weighted score >= 0.75
- Medium conviction: weighted score 0.50-0.74
- Low conviction: weighted score < 0.50

LEVEL EXTRACTION:
When sources mention specific levels, strikes, or targets, ALWAYS include them.
If a source says "watching 5950 support" → include "5950" in your output.
If a source mentions "Dec VIX 16 calls" → include the specific strike and expiry.

CONTRADICTION RESOLUTION:
When sources disagree, provide a WEIGHTED synthesis view:
"Given 42Macro (high weight) and Options Insight (high weight) both bullish vs YouTube (lower weight) bearish, the weighted view is moderately bullish with [specific conditions]."

CATALYST EXTRACTION:
Extract SPECIFIC DATES from content. "December FOMC" → "December 17-18 FOMC".
Rate each catalyst's expected impact on the thesis."""
```

#### 2. Update Synthesis Prompt

```python
def _build_synthesis_prompt_v2(self, content_items, time_window, focus_topic=None):
    """Build enhanced prompt for actionable synthesis."""

    # Group and summarize content by source (existing logic)
    content_section = self._format_content_section(content_items)

    prompt = f"""Analyze the following research content and generate an ACTIONABLE synthesis.

## Source Content (past {time_window})
{content_section}

## Required Output (JSON)

Generate a response with these sections:

### 1. market_regime (required)
{{
  "current": "risk-on|risk-off|transitioning|range-bound",
  "direction": "improving|deteriorating|stable",
  "confidence": 0.0-1.0,
  "key_drivers": ["driver1", "driver2", "driver3"]
}}

### 2. synthesis_summary (required)
2-3 sentence executive summary of the current research landscape.

### 3. tactical_ideas (required, array)
Ideas with <4 week time horizon. For EACH idea include:
- idea: clear statement
- conviction_score: {{"raw": "X/Y sources", "weighted": 0.0-1.0, "sources_agreeing": [...], "sources_disagreeing": [...]}}
- trade_structure: {{"instrument": "...", "direction": "...", "structure": "...", "entry_level": "...", "stop_level": "...", "target_level": "..."}}
- time_horizon: specific ("1-2 weeks", "through Dec FOMC", etc.)
- catalyst: what drives this
- invalidation: what would make this wrong
- rationale: 2-3 sentences

IMPORTANT: Extract SPECIFIC LEVELS from the source content. Do not use vague terms like "support" without the actual number.

### 4. strategic_ideas (required, array)
Ideas with 1-6 month horizon. Include:
- idea, conviction_score (same format)
- thesis: longer explanation
- key_levels: {{"support": [...], "resistance": [...]}}
- time_horizon, triggers, risks

### 5. watch_list (required, array)
Topics where sources DISAGREE or situation is developing:
- topic, status ("conflicting"|"developing"|"monitoring")
- bull_case: {{"view": "...", "sources": [...]}}
- bear_case: {{"view": "...", "sources": [...]}}
- resolution_trigger: what would resolve this
- action: recommended approach ("wait for X", "scale in if Y")

### 6. catalyst_calendar (required, array)
Upcoming events with SPECIFIC DATES:
- date: "YYYY-MM-DD"
- event: name
- impact: "high"|"medium"|"low"
- relevance: which ideas this affects
- consensus: market expectation
- risk: surprise scenario

### 7. source_summary (required)
Summary of sources analyzed with current stance of each.

Respond with valid JSON only. Be SPECIFIC with levels and dates."""

    return prompt
```

### Phase 2: Content Extraction Enhancement

#### 1. Pre-process Content for Level Extraction

```python
def _extract_levels_from_content(self, content_items: List[Dict]) -> Dict[str, List]:
    """
    Pre-scan content to extract specific levels, strikes, and dates.
    This helps Claude produce more specific output.
    """
    extracted = {
        "price_levels": [],
        "option_strikes": [],
        "dates": [],
        "tickers": []
    }

    import re

    for item in content_items:
        text = item.get("content_text", "") + " " + item.get("summary", "")

        # Extract price levels (e.g., "5950", "6000", "4.50")
        prices = re.findall(r'\b(\d{3,5}(?:\.\d{1,2})?)\b', text)
        extracted["price_levels"].extend(prices)

        # Extract option mentions (e.g., "Dec 16 calls", "Jan 4500 puts")
        options = re.findall(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+\s+(?:calls?|puts?))', text, re.I)
        extracted["option_strikes"].extend(options)

        # Extract dates
        dates = re.findall(r'((?:Jan|Feb|Mar|Dec|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?)', text, re.I)
        extracted["dates"].extend(dates)

        # Tickers already extracted by classifier
        tickers = item.get("tickers", [])
        extracted["tickers"].extend(tickers)

    # Deduplicate
    for key in extracted:
        extracted[key] = list(set(extracted[key]))

    return extracted
```

#### 2. Include Extracted Data in Prompt

```python
def _build_synthesis_prompt_v2(self, content_items, time_window, focus_topic=None):
    # ... existing content formatting ...

    # Add extracted levels section
    extracted = self._extract_levels_from_content(content_items)

    extraction_section = f"""
## Pre-Extracted Data (use these specific values in your output)

Price Levels Mentioned: {', '.join(extracted['price_levels'][:20])}
Option Strikes Mentioned: {', '.join(extracted['option_strikes'][:10])}
Dates Mentioned: {', '.join(extracted['dates'][:10])}
Tickers Mentioned: {', '.join(extracted['tickers'][:20])}

IMPORTANT: Incorporate these specific values into your tactical and strategic ideas rather than using vague language.
"""

    prompt = f"""...(existing prompt)...
{extraction_section}
...(rest of prompt)...
"""
```

### Phase 3: Database Schema Update

#### 1. Add version field to Synthesis table

```python
# In backend/models.py - Synthesis model

class Synthesis(Base):
    __tablename__ = "synthesis"

    id = Column(Integer, primary_key=True)
    synthesis_text = Column(Text)  # Keep for backwards compatibility
    synthesis_json = Column(Text)  # New: full JSON output
    schema_version = Column(String(10), default="2.0")  # New: track schema version
    key_themes = Column(Text)
    high_conviction_ideas = Column(Text)
    # ... existing fields ...
```

#### 2. Migration for existing data

```python
# Existing syntheses will have schema_version=None or "1.0"
# New syntheses will have schema_version="2.0"
# Frontend should handle both formats
```

### Phase 4: API Response Update

#### 1. Update synthesis endpoint response

```python
# In backend/routes/synthesis.py

@router.post("/generate")
async def generate_synthesis(request: SynthesisRequest, db: Session = Depends(get_db)):
    # ... existing logic ...

    # Use v2 synthesis
    result = agent.analyze_v2(content_items, time_window=request.time_window)

    # Store full JSON
    synthesis = Synthesis(
        synthesis_text=result.get("synthesis_summary", ""),
        synthesis_json=json.dumps(result),
        schema_version="2.0",
        # ... other fields ...
    )

    return {
        "status": "success",
        "synthesis_id": synthesis.id,
        "version": "2.0",
        **result
    }
```

### Phase 5: Frontend Display Update

#### 1. Update dashboard to render new format

```javascript
// In frontend/js/dashboard.js

function renderSynthesis(data) {
    if (data.version === "2.0") {
        return renderSynthesisV2(data);
    }
    return renderSynthesisV1(data);  // Legacy fallback
}

function renderSynthesisV2(data) {
    return `
        <div class="synthesis-v2">
            <div class="market-regime">
                <h3>Market Regime: ${data.market_regime.current}</h3>
                <span class="direction ${data.market_regime.direction}">
                    ${data.market_regime.direction}
                </span>
                <p>Key Drivers: ${data.market_regime.key_drivers.join(', ')}</p>
            </div>

            <div class="executive-summary">
                <p>${data.synthesis_summary}</p>
            </div>

            <div class="tactical-ideas">
                <h3>Tactical Ideas (< 4 weeks)</h3>
                ${data.tactical_ideas.map(renderTacticalIdea).join('')}
            </div>

            <div class="strategic-ideas">
                <h3>Strategic Ideas (1-6 months)</h3>
                ${data.strategic_ideas.map(renderStrategicIdea).join('')}
            </div>

            <div class="watch-list">
                <h3>Watch List</h3>
                ${data.watch_list.map(renderWatchItem).join('')}
            </div>

            <div class="catalyst-calendar">
                <h3>Catalyst Calendar</h3>
                ${renderCatalystTable(data.catalyst_calendar)}
            </div>
        </div>
    `;
}

function renderTacticalIdea(idea) {
    const conviction = idea.conviction_score;
    return `
        <div class="idea-card tactical">
            <div class="idea-header">
                <h4>${idea.idea}</h4>
                <span class="conviction ${getConvictionClass(conviction.weighted)}">
                    ${conviction.raw} (${(conviction.weighted * 100).toFixed(0)}%)
                </span>
            </div>

            <div class="trade-structure">
                <table>
                    <tr><td>Instrument:</td><td>${idea.trade_structure.instrument}</td></tr>
                    <tr><td>Direction:</td><td>${idea.trade_structure.direction}</td></tr>
                    <tr><td>Structure:</td><td>${idea.trade_structure.structure}</td></tr>
                    <tr class="entry"><td>Entry:</td><td>${idea.trade_structure.entry_level}</td></tr>
                    <tr class="stop"><td>Stop:</td><td>${idea.trade_structure.stop_level}</td></tr>
                    <tr class="target"><td>Target:</td><td>${idea.trade_structure.target_level}</td></tr>
                </table>
            </div>

            <div class="idea-meta">
                <span class="time-horizon">${idea.time_horizon}</span>
                <span class="catalyst">${idea.catalyst}</span>
            </div>

            <div class="rationale">${idea.rationale}</div>

            <div class="invalidation">
                <strong>Invalidation:</strong> ${idea.invalidation}
            </div>

            <div class="sources">
                Sources: ${conviction.sources_agreeing.join(', ')}
                ${conviction.sources_disagreeing.length > 0 ?
                    `<br>Disagreeing: ${conviction.sources_disagreeing.join(', ')}` : ''}
            </div>
        </div>
    `;
}
```

## Testing Plan

### Unit Tests

1. **Level Extraction Test**
   ```python
   def test_level_extraction():
       content = [{"content_text": "Watching 5950 support, targeting 6100"}]
       extracted = agent._extract_levels_from_content(content)
       assert "5950" in extracted["price_levels"]
       assert "6100" in extracted["price_levels"]
   ```

2. **Conviction Scoring Test**
   ```python
   def test_conviction_scoring():
       # Test that 42macro (1.5x) + discord (1.5x) vs youtube (0.8x)
       # Results in high conviction despite 2v1 raw count
       result = agent.analyze_v2(test_content)
       assert result["tactical_ideas"][0]["conviction_score"]["weighted"] > 0.75
   ```

### Integration Tests

1. Run synthesis with real collected data
2. Verify specific levels appear in output
3. Verify catalyst dates are specific
4. Verify conviction scores calculate correctly

### Manual Validation

1. Generate synthesis and review with domain expert
2. Verify extracted levels match source content
3. Verify trade structures are realistic and actionable

## Success Criteria

- [ ] Tactical ideas include specific entry/stop/target levels
- [ ] Conviction scores show X/Y source format + weighted percentage
- [ ] Time horizons are bucketed (tactical vs strategic)
- [ ] Catalyst calendar has specific dates (not "December FOMC" but "Dec 17-18")
- [ ] Watch list shows both bull/bear cases with resolution triggers
- [ ] Source weighting is applied and visible
- [ ] Synthesis generation stays under $0.10 per call
- [ ] Frontend displays new format cleanly
- [ ] Backwards compatibility with v1 syntheses

## Rollback Plan

If issues arise:
1. Agent maintains `analyze()` (v1) and `analyze_v2()` methods
2. API can switch via `?version=1` query parameter
3. Frontend handles both schema versions
4. Database stores both `synthesis_text` (v1) and `synthesis_json` (v2)

## Cost Impact

| Component | Current | Enhanced | Delta |
|-----------|---------|----------|-------|
| Prompt tokens | ~8,000 | ~10,000 | +25% |
| Output tokens | ~1,500 | ~3,000 | +100% |
| **Cost per synthesis** | ~$0.04 | ~$0.06 | +$0.02 |
| **Monthly (2x daily)** | ~$2.40 | ~$3.60 | +$1.20 |

## Implementation Checklist

- [ ] Update `SYSTEM_PROMPT` with v2 instructions
- [ ] Create `_build_synthesis_prompt_v2()` method
- [ ] Add `_extract_levels_from_content()` helper
- [ ] Create `analyze_v2()` method in SynthesisAgent
- [ ] Add `schema_version` to Synthesis model
- [ ] Update `/api/synthesis/generate` endpoint
- [ ] Update dashboard JavaScript for v2 rendering
- [ ] Add CSS styles for new synthesis display
- [ ] Test with real content
- [ ] Update CLAUDE.md documentation
- [ ] Update CHANGELOG

## Estimated Effort

| Task | Estimate |
|------|----------|
| Prompt engineering (system + synthesis) | 1.5 hours |
| Level extraction helper | 30 min |
| Agent v2 method | 30 min |
| Database schema update | 15 min |
| API endpoint update | 15 min |
| Frontend display update | 1.5 hours |
| Testing and validation | 1 hour |
| **Total** | ~5.5 hours |

## Future Enhancements (Out of Scope)

- Historical synthesis comparison ("what changed since last week")
- Alert system for conviction changes
- Integration with broker APIs for execution
- Mobile-optimized display
- PDF export of synthesis reports
