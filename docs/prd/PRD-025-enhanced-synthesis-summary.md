# PRD-025: Enhanced Synthesis Summary

## Overview

Expand the executive summary in v3 synthesis from a brief 2-4 sentence overview to a comprehensive multi-paragraph summary with per-source highlights, key takeaways, and macro context.

## Problem Statement

Current v3 synthesis executive summary is too brief:
- Only 2-4 sentences
- Doesn't capture enough detail from each source
- Users must dig into confluence zones and source stances for context
- Missing at-a-glance key takeaways

## Current State

Current `executive_summary` prompt in synthesis agent:

```
"executive_summary": {
  "narrative": "[2-4 sentences summarizing macro backdrop...]",
  "overall_tone": "[bullish|bearish|neutral|cautious]",
  "dominant_theme": "[Single most important theme]"
}
```

Output example:
```
"executive_summary": {
  "narrative": "Your sources are aligned on volatility expansion into FOMC.",
  "overall_tone": "cautious",
  "dominant_theme": "FOMC positioning"
}
```

## Proposed Enhancement

Expand to comprehensive multi-section summary:

```json
{
  "executive_summary": {
    "macro_context": "1-2 sentences on the overall macro backdrop...",
    "source_highlights": {
      "42macro": "2-3 sentences on 42Macro's current stance...",
      "discord": "2-3 sentences on Discord's current focus...",
      "kt_technical": "2-3 sentences on KT Technical's view...",
      "youtube": "1-2 sentences if relevant content...",
      "substack": "1-2 sentences if relevant content..."
    },
    "synthesis_narrative": "2-3 paragraphs synthesizing all sources, identifying where they align and conflict, and what the overall picture suggests...",
    "key_takeaways": [
      "Takeaway 1: Most important actionable insight",
      "Takeaway 2: Second most important insight",
      "Takeaway 3: Third insight",
      "Takeaway 4: Optional fourth insight",
      "Takeaway 5: Optional fifth insight"
    ],
    "overall_tone": "cautious",
    "dominant_theme": "FOMC volatility dynamics"
  }
}
```

## Detailed Section Specifications

### 1. Macro Context (1-2 sentences)

**Purpose**: Set the stage for what's happening in markets.

**Example**:
> Markets are navigating the final trading days before FOMC amid mixed signals on the inflation trajectory. The liquidity cycle appears to be rolling over while equity volatility remains compressed.

### 2. Source Highlights (per-source)

**Purpose**: Quick hit on what each source is currently focused on.

**Format**: 2-3 sentences per high-weight source, 1-2 for lower-weight sources.

**Example**:
```json
{
  "42macro": "42Macro continues to emphasize the r-star debate heading into December FOMC. They expect a 'hawkish cut' where the Fed delivers 25bp but signals a higher terminal rate. Their liquidity cycle framework suggests headwinds building into Q1.",

  "discord": "Imran is positioned for volatility expansion via VIX calendar spreads, expecting term structure normalization. Recent fade-the-rally trades in AAPL and broader market reflect a cautious tactical stance. Focus remains on FOMC as the key vol catalyst.",

  "kt_technical": "Elliott Wave analysis shows SPX testing key support at 6700-6750. A break opens the 6568-6677 zone as next target. Current levels represent a decision point in the wave count with the FOMC catalyst approaching.",

  "youtube": "Mixed macro commentary with some concern about liquidity rollover but also questioning Santa Claus rally dynamics.",

  "substack": "Long-term constructive on structural themes (AI, crypto) but acknowledging near-term volatility risks."
}
```

### 3. Synthesis Narrative (2-3 paragraphs)

**Purpose**: The heart of the synthesis - connecting the dots across all sources.

**Structure**:
- Paragraph 1: Where sources align (confluence)
- Paragraph 2: Where sources differ (conflicts) and what that means
- Paragraph 3: What deserves attention and why

**Example**:
> Your sources show notable confluence on volatility dynamics heading into the December FOMC. 42Macro's macro framework, Discord's tactical positioning, and KT Technical's decision-point wave count all point to this as the key event. The hawkish cut thesis (25bp cut with higher terminal rate signal) appears to be market consensus, creating a setup where surprises in either direction could drive significant moves.
>
> The main conflict centers on the Santa Claus rally narrative. YouTube commentary leans toward traditional year-end seasonality, while 42Macro and Discord are more skeptical given liquidity cycle concerns. KT Technical's chart work suggests the SPX 6700-6750 level will be the arbiter - holding would support the rally thesis, breaking would align with the cautious camp.
>
> The attention priorities are clear: VIX dynamics merit close watching with the FOMC catalyst days away, and SPX support levels (6700-6750 first, 6568-6677 if broken) are the key technical reference points. Discord's VIX calendar spread positioning represents a specific expression of the volatility expansion thesis that could inform tactical decisions.

### 4. Key Takeaways (3-5 bullet points)

**Purpose**: Scannable action items / main points.

**Format**: Numbered list, most important first.

**Example**:
```json
[
  "FOMC Dec 17-18 is the dominant catalyst with strong cross-source confluence on volatility expansion",
  "Hawkish cut (25bp + higher terminal rate signal) is consensus - watch for surprise in either direction",
  "SPX 6700-6750 is the key technical level; break opens 6568-6677 downside target",
  "VIX calendar spreads and fade-the-rally positioning reflect cautious tactical stance",
  "Santa Claus rally vs liquidity concerns remains an unresolved conflict to monitor"
]
```

### 5. Overall Tone & Dominant Theme

**Purpose**: Quick classification for at-a-glance assessment.

**Tone options**: bullish, bearish, neutral, cautious, uncertain, transitioning

**Dominant theme**: Single most important theme from the synthesis.

## Prompt Changes

### Updated V3 System Prompt Section

```python
V3_EXECUTIVE_SUMMARY_PROMPT = """
Generate a comprehensive executive summary with these sections:

1. MACRO CONTEXT (1-2 sentences)
Set the stage for what's happening in markets right now.

2. SOURCE HIGHLIGHTS (2-3 sentences per source)
For each source with content in this window, provide a focused summary of their current stance:
- 42Macro: Macro framework, liquidity cycle, key theses
- Discord: Tactical positioning, specific trades, market view
- KT Technical: Elliott Wave levels, chart patterns, key support/resistance
- YouTube: Macro commentary themes
- Substack: Research themes

3. SYNTHESIS NARRATIVE (2-3 paragraphs)
Connect the dots across all sources:
- Paragraph 1: Where sources align (confluence themes)
- Paragraph 2: Where sources differ and what that means
- Paragraph 3: What deserves attention and why

4. KEY TAKEAWAYS (3-5 bullet points)
Most important insights, ranked by importance.

5. OVERALL ASSESSMENT
- overall_tone: bullish|bearish|neutral|cautious|uncertain|transitioning
- dominant_theme: Single most important theme
"""
```

## Frontend Display

### Summary Section Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  SYNTHESIS SUMMARY                            Generated 2h ago  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  MACRO CONTEXT                                                  │
│  Markets are navigating the final trading days before FOMC...  │
│                                                                 │
│  ────────────────────────────────────────────────              │
│  SOURCE HIGHLIGHTS                                              │
│  ────────────────────────────────────────────────              │
│                                                                 │
│  🔵 42 Macro                                                    │
│  42Macro continues to emphasize the r-star debate heading      │
│  into December FOMC. They expect a 'hawkish cut' where the     │
│  Fed delivers 25bp but signals a higher terminal rate...       │
│                                                                 │
│  🟢 Discord (Imran)                                             │
│  Imran is positioned for volatility expansion via VIX          │
│  calendar spreads. Recent fade-the-rally trades reflect a      │
│  cautious tactical stance...                                   │
│                                                                 │
│  🟡 KT Technical                                                │
│  Elliott Wave analysis shows SPX testing key support at        │
│  6700-6750. A break opens the 6568-6677 zone...               │
│                                                                 │
│  ────────────────────────────────────────────────              │
│  SYNTHESIS                                                      │
│  ────────────────────────────────────────────────              │
│                                                                 │
│  Your sources show notable confluence on volatility dynamics   │
│  heading into the December FOMC. 42Macro's macro framework,    │
│  Discord's tactical positioning, and KT Technical's wave       │
│  count all point to this as the key event...                   │
│                                                                 │
│  The main conflict centers on the Santa Claus rally narrative. │
│  YouTube commentary leans toward seasonal strength, while      │
│  42Macro and Discord are more skeptical...                     │
│                                                                 │
│  ────────────────────────────────────────────────              │
│  KEY TAKEAWAYS                                                  │
│  ────────────────────────────────────────────────              │
│                                                                 │
│  1. FOMC Dec 17-18 is the dominant catalyst                    │
│  2. Hawkish cut is consensus - watch for surprises             │
│  3. SPX 6700-6750 is the key technical level                   │
│  4. VIX calendar spreads reflect cautious positioning          │
│  5. Santa rally vs liquidity remains unresolved                │
│                                                                 │
│  ────────────────────────────────────────────────              │
│  Overall: CAUTIOUS • Theme: FOMC Volatility Dynamics           │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Phase 1: Synthesis Agent Update

1. Update V3 system prompt with enhanced executive_summary structure
2. Update JSON schema validation
3. Test generation with sample content

### Phase 2: Frontend Update

1. Update synthesis display component to handle new structure
2. Add section styling for source highlights
3. Add numbered list styling for key takeaways
4. Handle backward compatibility with old v3 format

### Phase 3: MCP Update

1. Update `get_executive_summary` tool to return new structure
2. Add formatting for terminal/Claude Desktop display

## Backward Compatibility

- Old v3 syntheses with simple `narrative` field will continue to work
- Frontend should check for `source_highlights` presence and fall back to legacy display
- MCP tool should handle both formats gracefully

## Success Metrics

1. **Reduced reading time**: Users can scan summary without drilling into sections
2. **Per-source clarity**: Know what each source is saying at a glance
3. **Actionable takeaways**: Clear bullets for what matters most
4. **Better synthesis**: Multi-paragraph narrative connects dots better than 2-4 sentences

## Out of Scope

- Interactive summary features
- Summary customization/preferences
- Email/notification summaries (future enhancement)
- Voice summary generation

## Token Considerations

Enhanced summary will use more tokens:
- Current: ~200-300 tokens for executive_summary
- Proposed: ~600-800 tokens for executive_summary

This is acceptable given the significant improvement in user value. Total synthesis generation will increase from ~2000 to ~2500 tokens.
