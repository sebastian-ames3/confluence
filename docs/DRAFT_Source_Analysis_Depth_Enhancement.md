# Source Analysis Depth Enhancement - Draft Prompt Rewrites

**Status**: Draft for Discussion
**Created**: 2026-01-26
**Problem**: Source depth too shallow; Discord showing truncated JSON; missing regime triggers, invalidation criteria, and conditional logic

---

## Grounding Context

### Sources We're Working With

| Source | Channels/Content Types | Macro Purpose |
|--------|------------------------|---------------|
| **42Macro** | Leadoff Morning Note, Around The Horn, Macro Scouting Report, KISS Model | Regime framework, policy analysis, portfolio positioning |
| **Discord** | macro-daily, macro-weekly, spx-fixed-strike-vol, vix-monitor, crypto-weekly | Vol regime reads, positioning interpretation, tactical signals |
| **KT Technical** | Weekly blog posts with Elliott Wave analysis | Technical levels, cycle positioning, invalidation levels |
| **Substack** | Visser Labs | Thematic macro/crypto analysis |
| **YouTube** | Forward Guidance, Moonshots, Jordi Visser, 42Macro | Policy commentary, thematic context |

### Sample Content (KT Technical - from test fixtures)

```
KT Technical Analysis - December 13, 2024

GOOGL (Alphabet) - Elliott Wave Analysis:
We had a monster breakout from the 270 low. Looking at the wave structure, we're in
an intermediate degree wave 5 to the upside. Wave 4 appears to be completing with
support likely holding at the 0.236 fib level around 319. If we get deeper retracement,
the 0.382 fib at 313 should provide solid support. The 0.5 fib sits at 308.

Upside targets for wave 5 completion are looking at 328 to 330 zone. If we lose 310,
I'd be concerned, but the real invalidation is below 270 where weekly demand breaks.
That would negate the whole bullish count.

SPX (S&P 500):
The S&P is in wave 3 of an impulse structure. We're trending higher with good momentum.
Key support is at 5800, and if that holds, we target 6100 for wave 3 completion.
The hard invalidation is if we lose 5650 - that breaks the impulsive structure.
```

**What the current pipeline extracts:** "KT bullish on GOOGL and SPX, Elliott Wave analysis"

**What should be extracted:**
- Cycle position: Wave 3 (SPX), Wave 5 (GOOGL)
- Key levels: SPX support 5800, target 6100, invalidation 5650
- Conditional logic: "If we lose 310, I'd be concerned"
- Hard invalidation: "Below 270 negates bullish count"

---

## 1. 42Macro PDF Analyzer Prompt Rewrites

### Current System Prompt (Around The Horn)

**Location:** `agents/pdf_analyzer.py:606-618`

```python
"""You are analyzing a 42 Macro "Around The Horn" report.

This is a comprehensive macro research report covering multiple markets, sectors, and asset classes.
It contains the KISS Model portfolio positioning, regime analysis, and market commentary.

Focus on:
- Market regime assessment (growth/inflation quadrant)
- KISS Model portfolio positioning (equities, bonds, commodities, cash weights)
- Key macro themes and catalysts
- Specific sector/ticker recommendations
- Valuation metrics and positioning data

Be precise with numbers, dates, and specific recommendations."""
```

### PROPOSED System Prompt (Around The Horn)

```python
"""You are an institutional macro analyst extracting DECISION-RELEVANT information from a 42 Macro "Around The Horn" report.

This report contains Darius Dale's regime framework, KISS Model positioning, and macro analysis.

Your goal is NOT to summarize - it is to extract the DECISION ARCHITECTURE:
- What regime are we in?
- What would CHANGE the regime?
- What would INVALIDATE the current thesis?
- What are the CAUSAL CHAINS from policy to asset prices?

EXTRACT WITH PRECISION:
1. REGIME STATE
   - Current growth/inflation quadrant (Goldilocks, Reflation, Stagflation, Deflation)
   - Evidence cited for this classification
   - Confidence level expressed

2. REGIME TRIGGERS (Critical - this is what's currently being lost)
   - Specific conditions that would shift the regime
   - Format: "IF [condition] THEN [new regime/action]"
   - Include the actual thresholds mentioned (e.g., "Core PCE > 2.8%", not "inflation rises")

3. KISS MODEL POSITIONING
   - Exact allocation percentages (60/30/10/10, etc.)
   - What conditions would change these allocations
   - Time horizon for current positioning

4. THESIS INVALIDATION
   - Specific levels, data points, or events that would negate the current view
   - Format: "Thesis invalidated if [specific condition]"
   - Include hard stops vs. warning levels

5. POLICY TRANSMISSION CHAINS
   - How current Fed/BOJ/ECB policy flows through to asset prices
   - Format: "Policy X → Transmission mechanism → Asset impact"
   - Timeline for transmission

6. CONDITIONAL LOGIC
   - All "if/then" statements in the research
   - Scenario analysis mentioned
   - Contingent recommendations

Be SPECIFIC. Extract the decision rules, not conclusions."""
```

### PROPOSED Analysis Prompt Output Schema

**Location:** `agents/pdf_analyzer.py:719-751`

Replace the current flat schema with:

```python
prompt = f"""Analyze this 42 Macro investment research report.

**Source**: {source}
**Report Type**: {report_type}
**Date**: {metadata.get('date', 'Unknown')}

**Extracted Text**:
{truncated_text}

{tables_summary}

Extract information in this JSON structure - focus on DECISION ARCHITECTURE, not summaries:

{{
    "regime_state": {{
        "current_quadrant": "Goldilocks|Reflation|Stagflation|Deflation|Transitioning",
        "growth_assessment": "above_trend|trend|below_trend",
        "inflation_assessment": "above_trend|trend|below_trend",
        "confidence": "high|medium|low",
        "evidence_cited": ["specific data points supporting this classification"],
        "as_of_date": "date this assessment applies to"
    }},

    "regime_triggers": [
        {{
            "trigger_type": "shift|warning|confirmation",
            "condition": "SPECIFIC condition with numbers (e.g., 'Core PCE prints > 2.8% for 2 consecutive months')",
            "current_value": "current value of the metric if mentioned",
            "threshold": "the threshold value",
            "direction": "above|below|crosses",
            "would_shift_to": "new regime or stance",
            "recommended_action": "what to do if triggered",
            "time_relevance": "when this trigger matters"
        }}
    ],

    "kiss_positioning": {{
        "equities_pct": <number>,
        "bonds_pct": <number>,
        "commodities_pct": <number>,
        "cash_pct": <number>,
        "positioning_rationale": "why these weights",
        "rebalance_triggers": ["conditions that would change allocation"],
        "time_horizon": "tactical|strategic"
    }},

    "invalidation_criteria": [
        {{
            "severity": "thesis_ending|warning|monitoring",
            "condition": "SPECIFIC condition (e.g., 'SPX weekly close below 4680')",
            "what_it_invalidates": "which thesis or position this affects",
            "recommended_response": "what to do if this occurs"
        }}
    ],

    "policy_transmission": [
        {{
            "policy_action": "what the central bank is doing",
            "transmission_mechanism": "how it flows through (e.g., 'higher terminal rate → dollar strength → EM pressure')",
            "asset_impact": "which assets are affected and how",
            "timeline": "when the impact is expected",
            "current_stage": "where we are in the transmission"
        }}
    ],

    "conditional_logic": [
        {{
            "if_condition": "the IF part",
            "then_outcome": "the THEN part",
            "else_outcome": "alternative outcome if condition not met (if mentioned)",
            "context": "what this relates to"
        }}
    ],

    "key_themes": ["list of macro themes discussed"],
    "catalysts": [
        {{
            "event": "event name",
            "date": "specific date if mentioned",
            "expected_impact": "how it could affect regime/positioning",
            "scenarios": ["bull case", "bear case"]
        }}
    ],
    "tickers_mentioned": ["tickers with context"],
    "conviction": <0-10>,
    "time_horizon": "1d|1w|1m|3m|6m|6m+"
}}

CRITICAL INSTRUCTIONS:
- Extract DECISION RULES, not summaries
- Include SPECIFIC NUMBERS for all thresholds and levels
- Capture ALL conditional/if-then statements
- "Support levels" without numbers is USELESS - extract the actual level
- If the report says "if X happens, do Y" - that goes in conditional_logic
- If the report says "thesis is wrong if Z" - that goes in invalidation_criteria

Return ONLY valid JSON."""
```

---

## 2. Discord Macro Extraction Prompt (NEW)

### Current State

Discord content goes through the generic `ContentClassifierAgent` which:
1. Truncates to 1000 chars
2. Returns `{"classification": "simple_text", "detected_topics": [...], ...}`
3. Loses all macro-relevant structure

### PROPOSED: New Discord Macro Extractor

**Create new file:** `agents/discord_macro_extractor.py`

This agent runs on Discord content from high-priority macro channels INSTEAD OF generic classification.

```python
"""
Discord Macro Extractor Agent

Extracts macro-relevant intelligence from Discord messages.
Focuses on:
- Vol regime reads (compression/expansion/transition)
- Positioning interpretation (not the positions themselves)
- Key levels and their significance
- Market structure reads
- Cross-asset signals

Does NOT extract:
- Specific trade recommendations (user can get those directly)
- Strikes, expiries, position sizing
- RSI levels or other indicator values
"""

DISCORD_MACRO_SYSTEM_PROMPT = """You are extracting MACRO-RELEVANT intelligence from an options trader's Discord commentary.

This is NOT about extracting trade details (strikes, expiries, sizing) - the user can see those directly.
This IS about extracting the REGIME INTERPRETATION and MARKET STRUCTURE READS.

When Imran says "IV at 15 puts us in compression phase" - extract:
- Vol regime: compression
- IV level context: 15 is low end of range
- Implication: expansion likely on catalyst

When Imran says "skew is steep, put/call elevated" - extract:
- Positioning read: market hedged/cautious
- Implication: fuel for rally if catalyst hits

EXTRACT:
1. VOL REGIME ASSESSMENT
   - Current state: compression|expansion|transitioning|elevated|depressed
   - Evidence cited (IV levels, term structure shape, etc.)
   - What it implies for near-term

2. POSITIONING INTERPRETATION
   - How is the market positioned (not specific positions, but the read)
   - What does positioning imply (crowded, light, hedged, etc.)
   - Potential for positioning-driven moves

3. MARKET STRUCTURE READ
   - Current technical context
   - Key levels mentioned and WHY they matter
   - Support/resistance significance

4. CROSS-ASSET SIGNALS
   - Vol correlations mentioned
   - Cross-market tells (bonds, currencies, etc.)
   - Intermarket analysis

5. CONDITIONAL STATEMENTS
   - Any "if X then Y" logic
   - Scenario-dependent views
   - What would change the view

Be concise but capture the ANALYTICAL FRAMEWORK, not just conclusions."""


DISCORD_MACRO_EXTRACTION_PROMPT = """Analyze this Discord message from the {channel_name} channel.

**Author**: {author}
**Channel**: {channel_name} ({channel_description})
**Timestamp**: {timestamp}

**Message Content**:
{content}

{video_transcript_section}

Extract macro-relevant intelligence in JSON format:

{{
    "vol_regime": {{
        "state": "compression|expansion|transitioning|elevated|depressed|not_discussed",
        "iv_context": "description of current IV levels and what they mean",
        "term_structure": "contango|backwardation|flat|inverted|not_discussed",
        "skew_read": "steep|flat|inverted|not_discussed",
        "regime_implication": "what this vol setup implies for near-term"
    }},

    "positioning_read": {{
        "current_state": "description of how market is positioned",
        "evidence": ["what signals this positioning"],
        "implication": "what positioning implies for price action",
        "crowding_assessment": "crowded_long|crowded_short|balanced|light|not_discussed"
    }},

    "market_structure": {{
        "current_read": "overall technical/structure assessment",
        "key_levels": [
            {{
                "level": <number>,
                "type": "support|resistance|pivot|invalidation",
                "significance": "why this level matters",
                "timeframe": "intraday|daily|weekly"
            }}
        ],
        "trend_assessment": "bullish|bearish|neutral|range_bound"
    }},

    "cross_asset_signals": [
        {{
            "signal": "what cross-asset relationship is noted",
            "implication": "what it means for the primary asset"
        }}
    ],

    "conditional_logic": [
        {{
            "if_condition": "the condition",
            "then_outcome": "expected outcome",
            "context": "what this relates to"
        }}
    ],

    "key_levels_summary": {{
        "support": [<numbers>],
        "resistance": [<numbers>],
        "invalidation": [<numbers>]
    }},

    "overall_bias": "bullish|bearish|neutral|cautious",
    "confidence": "high|medium|low",
    "time_horizon": "intraday|days|weeks"
}}

INSTRUCTIONS:
- Focus on INTERPRETATION, not trade mechanics
- Extract the ANALYTICAL FRAMEWORK being applied
- Capture WHY levels matter, not just the numbers
- If content is just a trade call without macro context, mark vol_regime.state as "not_discussed"
- Video transcripts often contain the richest macro commentary - prioritize that content

Return ONLY valid JSON."""
```

### Channel-Specific Routing

Different Discord channels should emphasize different extraction:

| Channel | Primary Extraction Focus |
|---------|-------------------------|
| macro-daily | Vol regime, positioning read, market structure |
| macro-weekly | Regime assessment, cross-asset signals, conditional logic |
| spx-fixed-strike-vol | Vol regime (detailed), skew analysis, term structure |
| vix-monitor | VIX term structure, vol regime transitions |
| crypto-weekly | Vol regime (crypto), cross-asset (crypto/macro correlation) |
| stock-trades | Market structure, key levels (less macro depth expected) |

---

## 3. KT Technical Extraction Enhancement

### Current State

KT Technical goes through generic classification, losing:
- Elliott Wave cycle position
- Specific invalidation levels
- Conditional technical logic

### PROPOSED: Enhanced KT Extraction Prompt

```python
KT_TECHNICAL_SYSTEM_PROMPT = """You are extracting technical analysis intelligence from KT Technical's Elliott Wave analysis.

Focus on:
1. CYCLE POSITION - Where are we in the wave structure?
2. KEY LEVELS - Support, resistance, and crucially INVALIDATION levels
3. CONDITIONAL LOGIC - "If X breaks, then Y"
4. TIME PROJECTIONS - Wave completion targets and timing

Elliott Wave provides a FRAMEWORK for understanding where we are in market cycles.
The invalidation levels are CRITICAL - they tell us when the count is wrong."""


KT_TECHNICAL_EXTRACTION_PROMPT = """Analyze this KT Technical analysis content.

**Content**:
{content}

Extract in JSON format:

{{
    "instruments_analyzed": [
        {{
            "ticker": "symbol",
            "cycle_position": {{
                "current_wave": "wave count (e.g., 'Wave 3 of impulse', 'Wave 4 correction')",
                "degree": "primary|intermediate|minor",
                "trend_direction": "up|down|sideways",
                "cycle_stage": "early|mid|late"
            }},
            "key_levels": {{
                "support": [
                    {{"level": <number>, "description": "what fib/structure this represents"}}
                ],
                "resistance": [
                    {{"level": <number>, "description": "what this represents"}}
                ],
                "targets": [
                    {{"level": <number>, "description": "wave completion target"}}
                ],
                "invalidation": {{
                    "level": <number>,
                    "description": "what breaks if this level is lost",
                    "severity": "count_invalid|concerning|warning"
                }}
            }},
            "conditional_logic": [
                {{
                    "if_condition": "if we lose/break X",
                    "then_outcome": "what happens to the count/thesis"
                }}
            ],
            "bias": "bullish|bearish|neutral",
            "confidence": "high|medium|low"
        }}
    ],

    "cross_instrument_notes": ["any correlations or relative analysis mentioned"],
    "time_projections": ["any timing mentioned for wave completions"]
}}

CRITICAL:
- The INVALIDATION level is the most important extraction - it tells us when the analysis is WRONG
- Capture ALL "if we lose X" or "below X negates" statements
- Specific numbers only - "key support" without a number is useless

Return ONLY valid JSON."""
```

---

## 4. Synthesis Agent Prompt Updates

### Current Source Stance Extraction

**Location:** `agents/synthesis_agent.py:1038-1046`

```python
"source_stances": {
  "source_name": {
    "current_stance_narrative": "2-3 sentences in narrative form...",
    "key_themes": ["theme1", "theme2"],
    "overall_bias": "bullish|bearish|cautious|neutral|mixed"
  }
}
```

### PROPOSED: Enhanced Source Stance Schema

```python
"source_stances": {
    "42macro": {
        "weight": 1.5,
        "items_analyzed": 3,

        "regime_assessment": {
            "current_quadrant": "Goldilocks",
            "confidence": "high",
            "key_evidence": ["GDP above trend", "Core PCE moderating"]
        },

        "active_triggers": [
            {
                "condition": "Core PCE > 2.8% for 2 months",
                "would_cause": "Shift to Reflation quadrant",
                "current_status": "not triggered - Core PCE at 2.5%"
            }
        ],

        "invalidation_watches": [
            {
                "condition": "SPX weekly close below 4680",
                "would_invalidate": "Bull thesis",
                "current_status": "SPX at 5200 - not at risk"
            }
        ],

        "positioning": {
            "kiss_allocation": "60/30/10/10",
            "stance": "risk-on with hedges",
            "rationale": "Goldilocks regime supports equities"
        },

        "conditional_views": [
            {
                "if": "BOJ raises rates above 0.5%",
                "then": "Reduce EM exposure, watch yen crosses"
            }
        ],

        "current_stance_narrative": "Darius maintains Goldilocks regime call with 60% equity allocation...",
        "key_themes": ["Fed policy normalization", "Goldilocks regime"],
        "overall_bias": "bullish"
    },

    "discord": {
        "weight": 1.5,
        "items_analyzed": 15,

        "vol_regime": {
            "state": "compression",
            "iv_level": "15 (low end)",
            "implication": "Setup for expansion on catalyst"
        },

        "positioning_read": {
            "state": "Light positioning, elevated hedges",
            "implication": "Fuel for rally if catalyst"
        },

        "key_levels": {
            "support": [4700, 4680],
            "resistance": [4850],
            "invalidation": [4650]
        },

        "conditional_views": [
            {
                "if": "Break above 4800",
                "then": "Regime shift to expansion confirmed"
            }
        ],

        "current_stance_narrative": "Imran sees vol compression with light positioning...",
        "key_themes": ["Vol compression", "Positioning light"],
        "overall_bias": "cautiously bullish"
    },

    "kt_technical": {
        "weight": 1.2,
        "items_analyzed": 1,

        "cycle_assessment": {
            "primary_instrument": "SPX",
            "wave_position": "Wave 3 of impulse",
            "cycle_stage": "mid-cycle"
        },

        "key_levels": {
            "SPX": {
                "support": [5800],
                "target": [6100],
                "invalidation": 5650
            }
        },

        "invalidation_watches": [
            {
                "condition": "SPX below 5650",
                "would_invalidate": "Impulsive wave count"
            }
        ],

        "current_stance_narrative": "KT sees SPX in Wave 3 targeting 6100...",
        "key_themes": ["Wave 3 impulse", "Bullish structure"],
        "overall_bias": "bullish"
    }
}
```

---

## 5. Depth Limit Adjustments

### Current Limits

| Parameter | Location | Current |
|-----------|----------|---------|
| Classification truncation | `content_classifier.py:214` | 1000 chars |
| Synthesis summary truncation | `synthesis_agent.py:287,595,879,1199` | 500-800 chars |
| Items per source | `synthesis_agent.py:591,875` | 15 items |
| Source breakdown tokens | `synthesis_agent.py:1378` | 1500 tokens |

### PROPOSED Limits

| Parameter | Current | Proposed | Rationale |
|-----------|---------|----------|-----------|
| 42Macro summary truncation | 600 chars | 2000 chars | Regime triggers need full context |
| Discord (high-priority) summary | 600 chars | 1500 chars | Vol reads need detail |
| Discord (other) summary | 600 chars | 800 chars | Less macro depth expected |
| KT Technical summary | 600 chars | 1200 chars | Levels need precision |
| Items per source (42Macro) | 15 | 25 | More reports = more triggers |
| Items per source (Discord high-priority) | 15 | 25 | Real-time signals |
| Source breakdown tokens | 1500 | 2500 | Room for structured extraction |

---

## 6. Success Criteria

### 42Macro Output Should Include:

- [ ] Current regime quadrant with evidence
- [ ] At least 2-3 regime triggers with specific thresholds
- [ ] KISS allocation percentages (not just "overweight")
- [ ] At least 1-2 invalidation criteria with specific levels
- [ ] Policy transmission chain if discussed
- [ ] All conditional "if/then" statements from the report

**Example Good Output:**
```json
{
  "regime_state": {
    "current_quadrant": "Goldilocks",
    "evidence_cited": ["GDP 2.8% above trend", "Core PCE at 2.5% and falling"]
  },
  "regime_triggers": [
    {
      "condition": "Core PCE > 2.8% for 2 consecutive months",
      "would_shift_to": "Reflation",
      "current_value": "2.5%"
    }
  ],
  "invalidation_criteria": [
    {
      "condition": "SPX weekly close below 4680",
      "what_it_invalidates": "Bull market thesis"
    }
  ]
}
```

**Example Bad Output (Current State):**
```json
{
  "market_regime": "disinflationary_growth",
  "positioning": {"equities": "overweight"},
  "falsification_criteria": ["if inflation rises"]
}
```

### Discord Output Should Include:

- [ ] Vol regime state with IV context
- [ ] Positioning interpretation (not positions)
- [ ] Key levels with significance
- [ ] At least 1 conditional statement if present
- [ ] Cross-asset signals if mentioned

### KT Technical Output Should Include:

- [ ] Wave count and cycle position
- [ ] Support/resistance with specific numbers
- [ ] INVALIDATION level (critical)
- [ ] Conditional logic ("if we lose X")

---

## Implementation Order

1. **Phase 1: Prompt Rewrites** (Immediate)
   - Rewrite 42Macro system prompts and output schema
   - Create Discord macro extractor agent
   - Enhance KT Technical extraction prompt

2. **Phase 2: Depth Limits** (Same PR)
   - Increase truncation limits per source
   - Increase items per source selectively

3. **Phase 3: Synthesis Integration** (Follow-up PR)
   - Update synthesis prompts to use new structured fields
   - Update source_stances schema
   - Add regime state tracking

---

## Files to Modify

| File | Changes |
|------|---------|
| `agents/pdf_analyzer.py` | New system prompts (lines 606-665), new output schema (lines 706-751) |
| `agents/discord_macro_extractor.py` | **NEW FILE** - Discord-specific extraction |
| `agents/content_classifier.py` | Route Discord high-priority to new extractor |
| `agents/synthesis_agent.py` | Updated source_stances schema, increased limits |
| `backend/routes/synthesis.py` | Pass structured regime data through |

---

*This is a working draft for discussion. Specific numbers and thresholds should be validated against real content samples.*
