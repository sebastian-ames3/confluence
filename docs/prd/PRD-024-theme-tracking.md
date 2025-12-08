# PRD-024: Theme Tracking System

## Overview

Implement a structured theme tracking system that monitors how macro themes evolve over time, tracking per-source evidence without relying on pseudo-Bayesian conviction scores.

## Problem Statement

Current synthesis is stateless - each generation starts fresh with no memory of previous themes. This causes:

1. **Theme blindness**: Same themes appear repeatedly as "new" across syntheses
2. **Evolution invisibility**: Can't see how a theme (e.g., "FOMC hawkish cut") developed over weeks
3. **Source attribution loss**: Can't trace which source first identified a theme
4. **No lifecycle tracking**: Themes don't have a clear "emerging → active → evolved → dormant" arc

The existing database has `themes`, `theme_evidence`, and `bayesian_updates` tables, but they're unused.

## Design Principles

### What We're NOT Doing

- **No fake conviction scores**: Numerical "conviction" implies precision we don't have
- **No Bayesian theater**: Pseudo-math like `P(theme|evidence)` without real priors
- **No binary resolution**: Macro themes don't "resolve" - they evolve continuously

### What We ARE Doing

- **Structured evidence tracking**: Per-source, dated evidence with descriptive summaries
- **Theme lifecycle states**: emerging → active → evolved → dormant
- **Theme evolution chains**: Link evolved themes to their predecessors
- **Claude-based semantic matching**: Let AI determine if new evidence matches existing themes
- **Aggregate by idea**: Combine similar expressions of the same macro theme

## Schema Changes

### Modified `themes` Table

```sql
ALTER TABLE themes ADD COLUMN aliases TEXT;           -- JSON array of alternative expressions
ALTER TABLE themes ADD COLUMN evolved_from_theme_id INTEGER REFERENCES themes(id);
ALTER TABLE themes ADD COLUMN source_evidence TEXT;   -- JSON: per-source evidence summaries
ALTER TABLE themes ADD COLUMN catalysts TEXT;         -- JSON: linked upcoming events
ALTER TABLE themes ADD COLUMN first_source TEXT;      -- Source that first mentioned theme
ALTER TABLE themes ADD COLUMN last_updated_at TIMESTAMP;
```

**Remove columns** (or ignore):
- `current_conviction` - no longer used
- `confidence_interval_low/high` - not applicable
- `prior_probability` - fake Bayesian

### Source Evidence JSON Structure

```json
{
  "42macro": [
    {
      "date": "2025-12-01",
      "summary": "Highlighted liquidity cycle concerns, r-star debate ahead of FOMC",
      "raw_content_id": 456,
      "strength": "strong"  // "strong", "moderate", "weak"
    },
    {
      "date": "2025-12-05",
      "summary": "Reiterated hawkish cut thesis, expects Fed to signal higher terminal rate",
      "raw_content_id": 512,
      "strength": "strong"
    }
  ],
  "discord": [
    {
      "date": "2025-12-03",
      "summary": "VIX calendar spread positioning anticipating FOMC vol",
      "raw_content_id": 478,
      "strength": "moderate"
    }
  ]
}
```

### Theme Lifecycle States

```
emerging    → New theme with 1-2 sources, recently appeared
active      → Multiple sources discussing, ongoing relevance
evolved     → Theme has transformed (link to evolved_from_theme_id)
dormant     → No recent mentions, catalyst passed, or no longer relevant
```

## Theme Extraction Logic

### During Synthesis Generation

When `/api/synthesis/generate` runs:

1. **Extract themes from content**: Ask Claude to identify macro themes in the analyzed content
2. **Match against existing themes**: Use Claude to semantically match new themes to existing ones
3. **Update or create themes**:
   - If match found: Add new evidence to existing theme
   - If no match: Create new theme in "emerging" state
4. **Handle evolution**: If Claude detects a theme has evolved (e.g., "FOMC uncertainty" → "hawkish cut consensus"), create new theme with `evolved_from_theme_id`

### Theme Matching Prompt

```
Given these existing themes and a newly identified theme, determine if they match:

Existing themes:
1. "FOMC hawkish cut expectations" (active since 2025-11-15)
2. "Volatility expansion into year-end" (active since 2025-12-01)
3. "SPX corrective wave pattern" (emerging, 2025-12-05)

New theme to match: "Fed expected to deliver hawkish 25bp cut at December meeting"

Respond with:
- match_id: null if new theme, or ID of matching theme
- is_evolution: true if this represents evolution of an existing theme
- evolved_from_id: ID of theme this evolved from (if is_evolution)
- merge_suggestion: If very similar but not exact, suggest merge
```

### Manual Merge Capability

Users can merge themes through the UI:
- Select two similar themes
- Merge into primary theme
- Move all evidence from secondary to primary
- Add secondary theme name to aliases

## API Endpoints

### GET /api/themes

List all themes with optional filters.

```json
{
  "themes": [
    {
      "id": 1,
      "name": "FOMC hawkish cut expectations",
      "aliases": ["Fed December rate decision", "Hawkish 25bp cut"],
      "status": "active",
      "first_mentioned_at": "2025-11-15",
      "first_source": "42macro",
      "source_count": 4,
      "evidence_count": 12,
      "last_updated_at": "2025-12-06",
      "catalysts": ["2025-12-17 FOMC"]
    }
  ]
}
```

**Query params**:
- `status`: Filter by lifecycle state
- `source`: Filter by sources discussing
- `since`: Filter by first_mentioned_at

### GET /api/themes/{id}

Full theme detail with all evidence.

```json
{
  "id": 1,
  "name": "FOMC hawkish cut expectations",
  "aliases": ["Fed December rate decision"],
  "status": "active",
  "description": "Market expecting Fed to cut 25bp but signal higher terminal rate...",
  "first_mentioned_at": "2025-11-15",
  "first_source": "42macro",
  "evolved_from": null,
  "evolved_into": [{"id": 5, "name": "Post-FOMC rate path repricing"}],
  "source_evidence": {
    "42macro": [
      {"date": "2025-12-01", "summary": "...", "strength": "strong"},
      {"date": "2025-12-05", "summary": "...", "strength": "strong"}
    ],
    "discord": [
      {"date": "2025-12-03", "summary": "...", "strength": "moderate"}
    ]
  },
  "catalysts": [
    {"date": "2025-12-17", "event": "FOMC Decision", "impact": "high"}
  ],
  "last_updated_at": "2025-12-06"
}
```

### POST /api/themes/{id}/merge

Merge two themes.

```json
{
  "merge_into_id": 1,
  "theme_id_to_merge": 3
}
```

### PUT /api/themes/{id}/status

Update theme lifecycle status.

```json
{
  "status": "dormant",
  "reason": "FOMC catalyst passed, theme resolved"
}
```

## Frontend: Themes Tab

### Theme List View

```
┌─────────────────────────────────────────────────────────────────┐
│  THEMES                                        [Filter ▼] [+]   │
├─────────────────────────────────────────────────────────────────┤
│  ● FOMC hawkish cut expectations                    ACTIVE      │
│    First: 42macro (Nov 15) • 4 sources • 12 evidence           │
│    Catalyst: Dec 17 FOMC                                        │
├─────────────────────────────────────────────────────────────────┤
│  ○ Volatility expansion into year-end              ACTIVE      │
│    First: discord (Dec 1) • 3 sources • 8 evidence             │
│    Catalyst: Dec 17-18 FOMC                                     │
├─────────────────────────────────────────────────────────────────┤
│  ◐ SPX corrective wave pattern                     EMERGING    │
│    First: kt_technical (Dec 5) • 1 source • 3 evidence         │
│    Watching: 6700-6750 support                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Theme Detail View

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back to Themes                                               │
│                                                                 │
│  FOMC Hawkish Cut Expectations                                  │
│  Status: ACTIVE • Since Nov 15 • 4 sources                      │
│                                                                 │
│  Also known as:                                                 │
│  • Fed December rate decision                                   │
│  • Hawkish 25bp cut                                            │
│                                                                 │
│  ────────────────────────────────────────────────              │
│  EVIDENCE BY SOURCE                                             │
│  ────────────────────────────────────────────────              │
│                                                                 │
│  42 Macro (3 items)                                    ▼        │
│  ├─ Dec 5: Reiterated hawkish cut thesis...         [strong]   │
│  ├─ Dec 3: r-star debate framework...               [strong]   │
│  └─ Dec 1: First mention of hawkish cut...          [strong]   │
│                                                                 │
│  Discord (2 items)                                     ▼        │
│  ├─ Dec 5: VIX positioning ahead of Fed...          [moderate] │
│  └─ Dec 3: Vol expansion thesis...                  [moderate] │
│                                                                 │
│  KT Technical (1 item)                                 ▼        │
│  └─ Dec 4: FOMC decision point for wave count...    [weak]     │
│                                                                 │
│  ────────────────────────────────────────────────              │
│  RELATED CATALYSTS                                              │
│  ────────────────────────────────────────────────              │
│  Dec 17: FOMC Day 1                                             │
│  Dec 18: FOMC Decision + Press Conference                       │
│                                                                 │
│  [Mark Dormant]  [Merge with Another Theme]                     │
└─────────────────────────────────────────────────────────────────┘
```

## MCP Tools

### get_theme_summary

```json
{
  "active_themes": 5,
  "emerging_themes": 2,
  "themes": [
    {
      "name": "FOMC hawkish cut expectations",
      "status": "active",
      "sources": ["42macro", "discord", "kt_technical", "youtube"],
      "evidence_summary": "Strong consensus across sources on hawkish 25bp cut...",
      "next_catalyst": "Dec 17 FOMC"
    }
  ]
}
```

### get_theme_detail

Full theme with all evidence (same as API endpoint).

### search_themes

Search themes by keyword/topic.

## Implementation Steps

### Phase 1: Database Migration

1. Create migration to add new columns to themes table
2. Update backend models
3. Keep legacy columns for backward compatibility

### Phase 2: Theme Extraction

1. Add theme extraction to synthesis agent
2. Implement Claude-based semantic matching
3. Create/update themes during synthesis generation

### Phase 3: API Endpoints

1. Implement /api/themes endpoints
2. Add merge functionality
3. Add status update endpoint

### Phase 4: Frontend

1. Add Themes tab to navigation
2. Implement list view with filters
3. Implement detail view with evidence
4. Add merge and status update UI

### Phase 5: MCP Integration

1. Add theme tools to MCP server
2. Test with Claude Desktop

## Success Metrics

1. **Theme continuity**: Same macro theme isn't re-discovered across syntheses
2. **Evolution visibility**: Can see how "FOMC uncertainty" evolved to "hawkish cut consensus"
3. **Source attribution**: Know that 42Macro first identified a theme on specific date
4. **Lifecycle clarity**: Themes have clear states, old themes go dormant

## Out of Scope

- Automated conviction scoring
- Bayesian probability calculations
- Trade recommendations from themes
- Alert notifications on theme changes (future enhancement)

## Migration

Existing unused theme tables will be repurposed. No data loss expected since tables are currently empty.
