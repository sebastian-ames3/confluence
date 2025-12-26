# PRD-041: Tiered Synthesis

**Status**: In Progress
**Priority**: High
**Estimated Complexity**: Medium

## Overview

Enhance synthesis generation to provide three tiers of detail, solving the over-compression problem where valuable research signal is lost - particularly from YouTube where 10+ videos/week are reduced to 1-2 sentences.

## Problem Statement

The current V3 synthesis (`analyze_v3`) compresses content too aggressively:

1. **YouTube over-compression**: 10+ videos/week across 4 channels → single `source_stances.youtube` entry (2-3 sentences)
2. **Lost nuance**: Each video may discuss different topics, but synthesis picks only the "dominant" theme
3. **No per-content visibility**: User can't see what each individual piece of content contributed
4. **Single verbosity level**: No way to get more detail without losing the executive summary

The goal is to **reduce research consumption time, not reduce information** to the point of losing nuance.

## Solution: Three-Tier Synthesis

### Tier 1: Executive Summary (Current)
Quick overview for scanning - what's the overall picture?
- 2-3 paragraphs connecting themes across sources
- Key takeaways (3-5 bullets)
- Confluence zones and conflicts at a glance

### Tier 2: Source Breakdown (NEW)
Per-source detailed summaries with expandable content:
- **Per-channel summaries for YouTube** (Moonshots, Forward Guidance, etc.)
- **Key points from each source** (not just stance, but specific insights)
- **Content inventory** - titles of what was analyzed

### Tier 3: Content Detail (NEW)
Individual content item summaries:
- Each video, PDF, post gets its own 2-3 sentence summary
- Themes extracted from that specific content
- Click to see full analyzed content

## Design Decisions

### 1. YouTube Channel Granularity
- Each YouTube channel becomes its own "source" for Tier 2/3 display
- Moonshots, Forward Guidance, Jordi Visser Labs, 42 Macro each get separate breakdowns
- Tier 1 can still aggregate across all YouTube for the executive view

### 2. Expandable/Collapsible UI
- **Dashboard default**: Show Tier 1 (executive summary)
- **Click to expand**: Reveal Tier 2 source breakdowns
- **Click content title**: Reveal Tier 3 detail for that item

### 3. MCP Gets Full Detail
- MCP tools return Tier 1 + Tier 2 + Tier 3 by default
- No need to specify verbosity - Claude Desktop gets everything
- Keeps MCP interactions simple and information-rich

### 4. Storage Strategy
- Tier 1 (executive_summary): Stored in `syntheses` table as today
- Tier 2 (source_breakdowns): NEW field in synthesis JSON
- Tier 3 (content_summaries): Stored per-content in `analyzed_content.analysis_result`

## Technical Implementation

### 41.1 Enhanced Synthesis Schema

**File:** `agents/synthesis_agent.py`

Add new V4 method that generates all three tiers:

```python
def analyze_v4(
    self,
    content_items: List[Dict[str, Any]],
    older_content: Optional[List[Dict[str, Any]]] = None,
    time_window: str = "24h",
    focus_topic: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate tiered synthesis (V4 - PRD-041).

    Returns three tiers of detail:
    - executive_summary: High-level overview (Tier 1)
    - source_breakdowns: Per-source detailed summaries (Tier 2)
    - content_summaries: Per-content item summaries (Tier 3)
    """
```

### 41.2 New Response Schema

```python
{
    "version": "4.0",

    # TIER 1: Executive Summary (existing V3 structure, enhanced)
    "executive_summary": {
        "macro_context": "...",
        "synthesis_narrative": "...",  # 2-3 paragraphs
        "key_takeaways": [...],  # 3-5 bullets
        "overall_tone": "...",
        "dominant_theme": "..."
    },

    "confluence_zones": [...],  # Existing
    "conflict_watch": [...],  # Existing
    "attention_priorities": [...],  # Existing
    "catalyst_calendar": [...],  # Existing

    # TIER 2: Source Breakdowns (NEW)
    "source_breakdowns": {
        "42macro": {
            "weight": 1.5,
            "content_count": 3,
            "summary": "3-5 sentences covering key insights from 42Macro this period...",
            "key_insights": [
                "Specific insight 1 with levels/data",
                "Specific insight 2",
                "Specific insight 3"
            ],
            "themes": ["theme1", "theme2"],
            "overall_bias": "bullish|bearish|neutral",
            "content_titles": ["Title 1", "Title 2", "Title 3"]
        },
        "discord": { ... },
        "youtube:Moonshots": {  # Per-channel breakdown
            "weight": 0.8,
            "content_count": 4,
            "summary": "3-5 sentences on what Moonshots covered this week...",
            "key_insights": [
                "AI agents discussion point 1",
                "Technology trend insight 2"
            ],
            "themes": ["AI", "abundance"],
            "overall_bias": "bullish",
            "content_titles": ["Episode 1 Title", "Episode 2 Title", ...]
        },
        "youtube:Forward Guidance": { ... },
        "youtube:Jordi Visser Labs": { ... },
        "youtube:42 Macro": { ... },
        "kt_technical": { ... },
        "substack": { ... }
    },

    # TIER 3: Content Summaries (NEW - per-item detail)
    "content_summaries": [
        {
            "id": "content_id",
            "source": "youtube",
            "channel": "Moonshots",
            "title": "Episode Title",
            "collected_at": "2025-12-25T10:00:00Z",
            "summary": "2-3 sentence summary of THIS specific content...",
            "themes": ["AI agents", "workforce transformation"],
            "key_points": [
                "Point 1 from this content",
                "Point 2 from this content"
            ],
            "tickers_mentioned": ["NVDA", "MSFT"],
            "sentiment": "bullish"
        },
        ...
    ],

    # Metadata
    "time_window": "24h",
    "content_count": 25,
    "sources_included": ["42macro", "discord", "youtube", "kt_technical"],
    "youtube_channels_included": ["Moonshots", "Forward Guidance", "42 Macro"],
    "generated_at": "2025-12-26T12:00:00Z"
}
```

### 41.3 Two-Stage Generation

To handle the increased output, generate in two stages:

**Stage 1**: Executive Summary + Source Breakdowns (single Claude call)
- System prompt focuses on high-level synthesis
- Max tokens: 6000
- Output: Tiers 1 and 2

**Stage 2**: Content Summaries (process individually or in batches)
- For each content item, generate 2-3 sentence summary
- Can be done incrementally during content analysis (not at synthesis time)
- Store in `analyzed_content.analysis_result.content_summary`

This avoids hitting token limits while providing full detail.

### 41.4 Content-Level Summary Storage

**File:** `agents/content_classifier.py` or new processing step

When content is analyzed, also generate a standalone summary:

```python
content_summary = {
    "summary": "2-3 sentence summary of this content",
    "key_points": ["point1", "point2", "point3"],
    "themes": ["theme1", "theme2"],
    "tickers": ["NVDA"],
    "sentiment": "bullish"
}
# Store in analyzed_content.analysis_result.content_summary
```

This way, Tier 3 data is pre-computed, not generated at synthesis time.

### 41.5 API Endpoint Updates

**File:** `backend/routes/synthesis.py`

```python
@router.get("/api/synthesis/latest")
async def get_latest_synthesis(
    tier: int = Query(default=1, ge=1, le=3),
    db: Session = Depends(get_db)
):
    """
    Get latest synthesis.

    Args:
        tier: Level of detail (1=executive, 2=+source breakdowns, 3=+content summaries)
    """
    synthesis = await get_latest_from_db(db)

    if tier == 1:
        return filter_to_tier1(synthesis)
    elif tier == 2:
        return filter_to_tier2(synthesis)
    else:
        return synthesis  # Full Tier 3
```

### 41.6 Dashboard UI Updates

**File:** `frontend/index.html`, `frontend/js/synthesis.js`

```html
<!-- Tier 1: Always visible -->
<div class="synthesis-executive">
    <h2>Research Synthesis</h2>
    <div class="synthesis-narrative">...</div>
    <div class="key-takeaways">...</div>
</div>

<!-- Tier 2: Expandable source breakdowns -->
<div class="source-breakdowns collapsed">
    <h3 class="toggle-header">
        Source Breakdowns
        <span class="expand-icon">+</span>
    </h3>
    <div class="breakdown-content">
        <!-- Per-source cards -->
        <div class="source-card" data-source="42macro">
            <h4>42 Macro (3 items)</h4>
            <p class="source-summary">...</p>
            <ul class="key-insights">...</ul>
        </div>

        <div class="source-card" data-source="youtube:Moonshots">
            <h4>Moonshots (4 videos)</h4>
            <p class="source-summary">...</p>
            <ul class="key-insights">...</ul>
            <!-- Expandable content list -->
            <div class="content-list collapsed">
                <span class="toggle-content">Show videos</span>
                <ul class="tier3-items">
                    <li>Video 1: summary...</li>
                    <li>Video 2: summary...</li>
                </ul>
            </div>
        </div>

        <!-- Other sources... -->
    </div>
</div>
```

**JavaScript:**
```javascript
// Toggle Tier 2 visibility
document.querySelectorAll('.toggle-header').forEach(header => {
    header.addEventListener('click', () => {
        header.parentElement.classList.toggle('collapsed');
    });
});

// Toggle Tier 3 content list
document.querySelectorAll('.toggle-content').forEach(toggle => {
    toggle.addEventListener('click', () => {
        toggle.parentElement.classList.toggle('collapsed');
    });
});
```

**CSS:**
```css
.collapsed .breakdown-content,
.collapsed .tier3-items {
    display: none;
}

.source-card {
    background: var(--glass-bg);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
}

.toggle-header, .toggle-content {
    cursor: pointer;
    user-select: none;
}

.expand-icon {
    transition: transform 0.2s;
}

.source-breakdowns:not(.collapsed) .expand-icon {
    transform: rotate(45deg);
}
```

### 41.7 MCP Updates

**File:** `mcp/server.py`

Update `get_latest_synthesis` tool to return full detail:

```python
@tool
def get_latest_synthesis() -> Dict:
    """
    Get the complete research synthesis with all tiers of detail.

    Returns:
    - Executive summary (macro context, key takeaways)
    - Source breakdowns (per-source summaries including per-channel YouTube)
    - Content summaries (per-item detail)
    - Confluence zones, conflicts, attention priorities
    - Catalyst calendar
    """
    # Always return full Tier 3 data
    return api_client.get_synthesis(tier=3)
```

## File Changes

### New Files
- `frontend/js/synthesis-tiers.js` - Tier expansion logic

### Modified Files
- `agents/synthesis_agent.py` - Add `analyze_v4()` method
- `backend/routes/synthesis.py` - Add tier parameter, update response building
- `frontend/index.html` - Expandable synthesis UI
- `frontend/css/main.css` - Tier expansion styling
- `mcp/server.py` - Update `get_latest_synthesis` to return full detail
- `CLAUDE.md` - Document new synthesis tiers

## Testing

### Unit Tests (`tests/test_prd041_tiered_synthesis.py`)
- V4 synthesis returns all three tiers
- YouTube channels get individual breakdowns (not grouped)
- Source breakdowns include content_count and content_titles
- Content summaries include per-item detail
- Empty content returns proper empty structure
- Tier parameter filters response correctly

### Integration Tests
- API returns correct tier based on parameter
- MCP returns full Tier 3 by default
- Content summaries stored during analysis are retrieved at synthesis time

### UI Tests (`tests/playwright/synthesis-tiers.spec.js`)
- Tier 1 visible by default
- Click header expands Tier 2
- Each source card shows summary and key insights
- YouTube channels shown separately (Moonshots, Forward Guidance, etc.)
- Click "Show videos" expands Tier 3 content list
- Collapse/expand animations work
- Mobile responsive

## Success Metrics

1. **Information fidelity**: YouTube insights no longer lost - each channel represented
2. **User control**: Can scan quickly (Tier 1) or dive deep (Tier 2/3)
3. **MCP richness**: Claude Desktop gets full context without prompting

## Definition of Done

### Synthesis Agent
- [ ] `analyze_v4()` method implemented
- [ ] Returns executive_summary (Tier 1)
- [ ] Returns source_breakdowns (Tier 2) with per-channel YouTube
- [ ] Returns content_summaries (Tier 3) or references to stored summaries
- [ ] Two-stage generation handles token limits

### Content-Level Summaries
- [ ] Content analysis stores per-item summary in `analysis_result.content_summary`
- [ ] Summary includes: summary, key_points, themes, tickers, sentiment
- [ ] Summaries retrieved at synthesis time for Tier 3

### API
- [ ] `/api/synthesis/latest` accepts `tier` parameter (1, 2, 3)
- [ ] Default tier=1 for backwards compatibility
- [ ] Tier 3 includes full content_summaries array

### Dashboard UI
- [ ] Tier 1 (executive summary) visible by default
- [ ] "Source Breakdowns" header is clickable, expands Tier 2
- [ ] Each source has its own card with summary + key insights
- [ ] YouTube channels shown separately (not grouped)
- [ ] "Show content" expands Tier 3 list within each source
- [ ] Smooth animations for expand/collapse
- [ ] Works on mobile

### MCP
- [ ] `get_latest_synthesis` returns all three tiers by default
- [ ] No verbosity parameter needed

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Playwright UI tests pass

### Documentation
- [ ] CLAUDE.md updated with tiered synthesis info
- [ ] PRD moved to archived on completion

## Rollout

1. **Phase 1**: Content-level summaries
   - Update content analysis to store per-item summaries
   - Backfill existing content (optional)

2. **Phase 2**: Synthesis agent V4
   - Implement `analyze_v4()` with source breakdowns
   - YouTube channel separation

3. **Phase 3**: API + Dashboard
   - Add tier parameter to API
   - Expandable UI components

4. **Phase 4**: MCP + Testing
   - Update MCP to return full detail
   - Full test coverage

---

*Created: 2025-12-26*
