# PRD-021: Research Consumption Hub

## Overview

Transform the synthesis output from a "trade idea generator" to a "research consumption assistant" that helps users efficiently digest multiple paid research sources, identify confluence, and know where to focus attention.

## Problem Statement

Users subscribe to multiple research services (Discord, 42Macro, KT Technical, YouTube, Substack). Each publishes regularly, creating:

1. **Volume overwhelm** - Too much content to consume in real-time
2. **Memory decay** - Hard to remember what was said last week vs this week
3. **Manual dot-connection** - Difficult to link macro backdrop to tactical ideas across sources
4. **Relevance timing** - Content published days ago may become critical today

## Solution

A research consumption assistant that answers:

| Question | Feature |
|----------|---------|
| "What are my sources saying?" | Executive Summary |
| "Where do they agree?" | Confluence Zones |
| "Where do they disagree?" | Conflict Watch |
| "What deserves my attention?" | Attention Priorities |
| "What should I re-review?" | Re-Review Recommendations |

## Source Landscape

Understanding the user's sources is critical to the synthesis approach:

| Source | Content Type | Provides Trade Ideas? |
|--------|--------------|----------------------|
| Discord (Imran) | Options flow, tactical positioning | **Yes** - specific trades |
| KT Technical | Elliott Wave on 10 instruments | **Sometimes** - levels align |
| 42Macro | Macro regime, liquidity cycles | **No** - backdrop only |
| YouTube | Macro commentary | **No** - backdrop only |
| Substack | Thematic research | **No** - backdrop only |

**Key insight**: Only 1-2 sources suggest trades. The others provide macro context that either supports or contradicts those ideas. Confluence means "does the macro backdrop support the tactical positioning?"

## Revised Output Schema

### 1. Executive Summary

**Purpose**: Descriptive summary of what sources are saying (not prescriptive trading advice)

```json
{
  "executive_summary": {
    "narrative": "Your macro sources (42Macro, Substack) are highlighting liquidity cycle concerns heading into FOMC. Your tactical source (Discord) is positioning for volatility expansion via VIX structures. KT Technical shows SPX testing key Elliott Wave support at 6700-6750. There's alignment on the volatility thesis but conflict on whether Santa Claus rally materializes.",
    "overall_tone": "cautious",
    "key_theme": "Volatility expansion into FOMC"
  }
}
```

**Tone**: Should read like a research briefing, not trading instructions.

### 2. Confluence Zones

**Purpose**: Show where independent sources align on themes/views (replaces "tactical_ideas")

```json
{
  "confluence_zones": [
    {
      "theme": "Volatility expansion into FOMC",
      "confluence_strength": 0.85,
      "sources_aligned": [
        {
          "source": "discord",
          "view": "VIX calendar spread positioning, fade-the-rally stance"
        },
        {
          "source": "42macro",
          "view": "Liquidity cycle concerns, policy uncertainty"
        },
        {
          "source": "kt_technical",
          "view": "Key support tests, decision point in wave count"
        }
      ],
      "sources_contrary": [],
      "relevant_levels": ["VIX 16-17 current", "SPX 6700-6750 support"],
      "related_catalyst": "Dec 17-18 FOMC"
    },
    {
      "theme": "SPX downside risk to 6568-6677",
      "confluence_strength": 0.65,
      "sources_aligned": [
        {
          "source": "kt_technical",
          "view": "Elliott Wave support zone at 6568-6677"
        },
        {
          "source": "discord",
          "view": "Fade-the-rally positioning in AAPL and broader market"
        }
      ],
      "sources_contrary": [
        {
          "source": "42macro",
          "view": "Not calling for imminent crash, watching for resolution"
        }
      ],
      "relevant_levels": ["6700-6750 first support", "6568-6677 next zone"],
      "related_catalyst": null
    }
  ]
}
```

**Key change**: Shows "where sources agree" not "what trade to take"

### 3. Conflict Watch

**Purpose**: Surface unresolved debates in the research (keep from v2, works well)

```json
{
  "conflict_watch": [
    {
      "topic": "Santa Claus rally vs liquidity concerns",
      "status": "active_conflict",
      "bull_case": {
        "view": "Traditional year-end rally, Fed engineering positive sentiment",
        "sources": ["youtube"]
      },
      "bear_case": {
        "view": "Liquidity cycle rolling over, crypto/commodities weakness signaling risk-off",
        "sources": ["42macro", "discord"]
      },
      "resolution_trigger": "December FOMC outcome and year-end flows",
      "weighted_lean": "slight_bear",
      "user_action": "Monitor - this conflict affects VIX and SPX positioning"
    }
  ]
}
```

### 4. Attention Priorities (NEW)

**Purpose**: Ranked list of what deserves focus this week

```json
{
  "attention_priorities": [
    {
      "rank": 1,
      "focus_area": "VIX / Volatility Dynamics",
      "why": "Strong confluence (3/5 sources), FOMC catalyst Dec 17-18 approaching",
      "sources_discussing": ["discord", "42macro", "kt_technical"],
      "time_sensitivity": "high"
    },
    {
      "rank": 2,
      "focus_area": "SPX Support Levels (6700-6750)",
      "why": "Currently testing, KT Technical wave count decision point",
      "sources_discussing": ["kt_technical", "discord"],
      "time_sensitivity": "immediate"
    },
    {
      "rank": 3,
      "focus_area": "Crypto/BTC Correlation",
      "why": "Developing thesis on liquidity correlation, watch for breakdown",
      "sources_discussing": ["42macro", "substack", "youtube"],
      "time_sensitivity": "medium"
    }
  ]
}
```

**Ranking factors**:
- Confluence strength (more sources = higher priority)
- Catalyst proximity (sooner = higher priority)
- Current market relevance (testing levels now = higher priority)

### 5. Re-Review Recommendations (NEW)

**Purpose**: Identify older content that's NOW highly relevant

```json
{
  "re_review_recommendations": [
    {
      "source": "42macro",
      "content_date": "2025-12-01",
      "title": "FOMC Positioning Framework",
      "why_relevant_now": "The hawkish cut scenario they outlined is now market consensus. Their framework for interpreting Powell's language on r* is directly applicable to Dec 17-18.",
      "themes_mentioned": ["FOMC", "r-star", "hawkish cut"],
      "relevance_trigger": "catalyst_approaching"
    },
    {
      "source": "kt_technical",
      "content_date": "2025-11-28",
      "title": "SPX Elliott Wave Update",
      "why_relevant_now": "We're now testing the 6700 support level they identified. Review their wave count and next targets at 6568-6677.",
      "themes_mentioned": ["SPX", "Elliott Wave", "support levels"],
      "relevance_trigger": "level_being_tested"
    },
    {
      "source": "discord",
      "content_date": "2025-11-30",
      "title": "VIX Term Structure Discussion",
      "why_relevant_now": "The calendar spread setup they described is now at the entry conditions they specified. Worth reviewing the specific thesis and structure.",
      "themes_mentioned": ["VIX", "calendar spreads", "term structure"],
      "relevance_trigger": "setup_conditions_met"
    }
  ]
}
```

**Relevance triggers**:
- `catalyst_approaching`: Event discussed is now imminent
- `level_being_tested`: Price level mentioned is now in play
- `scenario_playing_out`: Thesis outlined is now materializing
- `conflict_resolving`: Debate flagged is getting clarity

**Implementation**: Synthesis must query content OLDER than the synthesis window (e.g., 14-30 days back) and compare against current themes/levels.

### 6. Source Stances (Enhanced)

**Purpose**: Narrative summary of what each source is currently thinking

```json
{
  "source_stances": {
    "discord": {
      "weight": 1.5,
      "items_analyzed": 14,
      "current_stance_narrative": "Imran is tactically positioned for volatility expansion. He sees the market as too complacent heading into FOMC and is expressing this via VIX calendar spreads and fading equity rallies. Key focus on term structure normalization.",
      "key_themes": ["VIX", "calendar spreads", "fade rallies"],
      "overall_bias": "cautious_bearish"
    },
    "42macro": {
      "weight": 1.5,
      "items_analyzed": 5,
      "current_stance_narrative": "Focused on the liquidity cycle potentially rolling over. Watching the r* debate at FOMC closely. They see macro headwinds building but are not calling for an imminent crash - more of a 'deteriorating conditions' stance.",
      "key_themes": ["liquidity cycle", "FOMC", "r-star"],
      "overall_bias": "macro_cautious"
    },
    "kt_technical": {
      "weight": 1.2,
      "items_analyzed": 10,
      "current_stance_narrative": "Elliott Wave analysis shows SPX in a corrective wave pattern with key support at 6700-6750. A break opens 6568-6677 as next target. The current level represents a decision point for the wave count.",
      "key_themes": ["SPX", "Elliott Wave", "support levels"],
      "overall_bias": "watching_for_breakdown"
    },
    "youtube": {
      "weight": 0.8,
      "items_analyzed": 15,
      "current_stance_narrative": "Mixed macro outlook. Some concern about liquidity cycle rollover but also questioning whether the Fed can engineer a Santa Claus rally. More observational than directional.",
      "key_themes": ["macro", "Fed policy", "Santa rally"],
      "overall_bias": "neutral_uncertain"
    },
    "substack": {
      "weight": 1.0,
      "items_analyzed": 15,
      "current_stance_narrative": "Long-term constructive on AI and crypto disruption themes but acknowledging near-term volatility and regime transition risks. More focused on structural trends than tactical positioning.",
      "key_themes": ["AI", "crypto", "structural trends"],
      "overall_bias": "long_term_bullish"
    }
  }
}
```

**Key change**: Narrative format reads like "what is this person/source thinking" rather than bullet points.

### 7. Catalyst Calendar (Enhanced)

**Purpose**: Upcoming events with source linkage

```json
{
  "catalyst_calendar": [
    {
      "date": "2025-12-06",
      "event": "NFP Employment Report",
      "impact": "medium",
      "source_perspectives": [
        {
          "source": "42macro",
          "view": "Watching for labor market normalization, affects Fed path"
        }
      ],
      "themes_affected": ["Fed policy", "volatility"],
      "pre_event_review": "42Macro Dec 2 labor market framework"
    },
    {
      "date": "2025-12-11",
      "event": "CPI Inflation Report",
      "impact": "high",
      "source_perspectives": [
        {
          "source": "42macro",
          "view": "Key input for FOMC decision, watching for disinflation continuation"
        },
        {
          "source": "discord",
          "view": "Positioned for vol expansion if surprise"
        }
      ],
      "themes_affected": ["FOMC", "volatility", "rate-sensitive"],
      "pre_event_review": null
    },
    {
      "date": "2025-12-17",
      "event": "FOMC Day 1",
      "impact": "high",
      "source_perspectives": [
        {
          "source": "42macro",
          "view": "Expects hawkish cut, watching r* language"
        },
        {
          "source": "discord",
          "view": "Peak vol expansion expected around this event"
        },
        {
          "source": "kt_technical",
          "view": "Decision point for SPX wave count"
        }
      ],
      "themes_affected": ["volatility", "SPX levels", "positioning"],
      "pre_event_review": "42Macro FOMC Framework (Dec 1)"
    }
  ]
}
```

**Key addition**: `source_perspectives` shows exactly what each source said about the catalyst, and `pre_event_review` links to relevant content to review beforehand.

## Implementation Changes

### Synthesis Agent Updates

1. **System prompt rewrite**: Shift from "generate trade ideas" to "synthesize research and identify confluence"

2. **Extended content query**: For re-review recommendations, query content 14-30 days back (not just synthesis window)

3. **Theme extraction enhancement**: Better extraction of:
   - Price levels mentioned
   - Catalysts discussed
   - Scenarios outlined
   - Directional bias

4. **Confluence calculation**: Instead of "X/Y sources agree on this trade idea", calculate "X/Y sources align on this theme/view"

### Database Changes

None required - current schema supports this output in `synthesis_json` column.

### Frontend Changes

1. **Executive Summary**: Prominent narrative at top
2. **Confluence Zones**: Visual grouping of aligned sources
3. **Attention Priorities**: Numbered/ranked list
4. **Re-Review Section**: Cards with source, date, why relevant
5. **Source Stances**: Expandable narrative cards
6. **Catalyst Calendar**: Timeline with source perspective tooltips

## User Workflow

**Daily routine (5-10 minutes)**:

1. Open dashboard
2. Read executive summary → "What's the overall picture?"
3. Scan confluence zones → "Where do my sources agree?"
4. Check conflict watch → "What's unresolved?"
5. Review attention priorities → "Where should I focus today?"
6. Check re-review recommendations → "What older content should I revisit?"
7. Glance at catalyst calendar → "What's coming up?"

**Result**: User has effectively "consumed" all their research and knows exactly where to dig deeper.

## Success Metrics

1. **Reduced consumption time**: User spends less time reading/watching raw content
2. **Increased confluence awareness**: User identifies cross-source alignment they would have missed
3. **Better recall**: Re-review feature surfaces forgotten but relevant content
4. **Clear prioritization**: User knows what deserves attention vs what to deprioritize

## Out of Scope

- Trade execution recommendations (entry/stop/target)
- Position sizing suggestions
- Risk/reward calculations
- Strike selection for options
- Portfolio construction advice

The tool surfaces what the research says. The user decides what to do with it.

## Migration from v2

- Keep source weighting system (works well)
- Keep catalyst calendar structure (enhance with source linkage)
- Keep conflict watch (works well)
- Replace tactical_ideas with confluence_zones
- Replace strategic_ideas with enhanced confluence_zones
- Add attention_priorities (new)
- Add re_review_recommendations (new)
- Enhance source_summary to source_stances (narrative format)

## Schema Version

This will be schema version "3.0" stored in `synthesis.schema_version`.

Backwards compatibility:
- v1.0: Legacy synthesis (text + themes)
- v2.0: Actionable synthesis (trade ideas)
- v3.0: Research consumption hub (confluence + re-review)

Frontend should handle all three versions gracefully.
