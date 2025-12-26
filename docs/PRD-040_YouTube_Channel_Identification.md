# PRD-040: YouTube Channel Identification

**Status**: Complete
**Priority**: Medium
**Estimated Complexity**: Low-Medium

## Overview

Enhance synthesis generation to attribute YouTube content to specific channel names rather than the generic "Youtube" source. This improves clarity when multiple YouTube channels discuss different topics, allowing users to understand which show/podcast provided specific insights.

## Problem Statement

Currently, the system monitors 4 YouTube channels:
- Peter Diamandis (Moonshots podcast)
- Jordi Visser Labs
- Forward Guidance
- 42 Macro

However, all content from these channels is attributed to the generic source "Youtube" in synthesis output:

> "Youtube noted that AI agents could reshape the workforce..."

This is problematic because:
1. **Lost attribution**: Users don't know which channel/show provided the insight
2. **Different perspectives conflated**: Moonshots (AI-focused) vs Forward Guidance (macro-focused) have different domains
3. **Podcast guests ignored**: Moonshots has 3-5 "Moonshot Mates" guests per episode - attributing to "Peter Diamandis" would be inaccurate

## Solution

Attribute content to the **channel/show name** rather than individual hosts:

| Channel Key | Display Name | Domain |
|-------------|--------------|--------|
| `peter_diamandis` | Moonshots | AI, technology, abundance |
| `jordi_visser` | Jordi Visser Labs | Information synthesis, macro |
| `forward_guidance` | Forward Guidance | Macroeconomics, Fed policy |
| `42macro` | 42 Macro | Institutional macro research |

Synthesis output becomes:
> "Moonshots explored how AI agents could reshape the workforce, while Forward Guidance focused on Fed policy implications..."

## Design Decisions

### 1. Channel-Level Attribution (Not Speaker-Level)
- Attribute to show/channel name, not individual hosts
- Avoids need for speaker diarization (overkill for this tool)
- Accurate for podcasts with multiple guests (Moonshots)

### 2. Equal Weighting
- All YouTube channels share the same weight (0.8x)
- No channel is considered more authoritative than another
- Simplifies implementation and avoids bias

### 3. Preserve Source Type for Confluence Logic
- Keep `source` = "youtube" for weighting and confluence calculations
- Add `channel` field for display/attribution purposes
- All YouTube channels still count as one "youtube" source type for confluence detection

### 4. Backwards Compatible
- Existing data with `channel_name` in metadata works automatically
- Falls back to "Youtube" if channel_name not present in older records
- No database migration required

## Technical Implementation

### 40.1 Channel Display Name Mapping

**File:** `backend/routes/synthesis.py`

```python
# YouTube channel display names for synthesis attribution
YOUTUBE_CHANNEL_DISPLAY = {
    "peter_diamandis": "Moonshots",
    "jordi_visser": "Jordi Visser Labs",
    "forward_guidance": "Forward Guidance",
    "42macro": "42 Macro"
}
```

### 40.2 Content Item Enhancement

**File:** `backend/routes/synthesis.py`

Modify `_get_content_for_synthesis()` to extract channel information:

```python
# Current
content_items.append({
    "source": source.name,  # Always "youtube"
    ...
})

# Enhanced
channel_name = None
channel_display = None
if source.name == "youtube":
    channel_name = metadata.get("channel_name")
    channel_display = YOUTUBE_CHANNEL_DISPLAY.get(channel_name, channel_name)

content_items.append({
    "source": source.name,  # Keep "youtube" for weighting
    "channel": channel_name,  # Raw channel key
    "channel_display": channel_display or source.name.title(),  # Display name
    ...
})
```

### 40.3 Synthesis Agent Prompt Updates

**File:** `agents/synthesis_agent.py`

Update prompt building to use channel names for YouTube content:

```python
# Current grouping
for source, items in by_source.items():
    weight = self.SOURCE_WEIGHTS_V2.get(source, 1.0)
    content_section += f"\n### {source.upper()} (Weight: {weight}x)\n"

# Enhanced grouping for YouTube
# Group YouTube content by channel_display instead of just "youtube"
```

Update `SOURCE_CONTEXT` in system prompts:

```python
# Current
"- YouTube: Macro commentary - provides backdrop/context, NOT trade ideas"

# Enhanced
"- YouTube channels (Moonshots, Jordi Visser Labs, Forward Guidance, 42 Macro): " \
"Macro commentary and perspectives - provides backdrop/context, NOT trade ideas"
```

### 40.4 Synthesis Response Enhancement

Update `sources_included` in synthesis response to include channel attribution:

```python
# Option A: Keep simple (recommended for backwards compatibility)
"sources_included": ["youtube", "discord", "42macro"]

# Option B: Include channel detail (if needed for UI)
"youtube_channels": ["Moonshots", "Forward Guidance"]
```

### 40.5 UI Display Updates

**File:** `frontend/index.html` (or relevant JS files)

When displaying synthesis content that references sources, show channel names instead of "Youtube" where available.

## Files Modified

| File | Changes |
|------|---------|
| `backend/routes/synthesis.py` | Add channel mapping, enhance `_get_content_for_synthesis()` |
| `agents/synthesis_agent.py` | Update prompt building and source context |
| `frontend/index.html` | Display channel names in synthesis UI |
| `tests/test_prd040_youtube_channels.py` | New test file |

## Test Plan

### Backend Tests

1. **Channel mapping tests**
   - Verify all 4 channels have display names
   - Verify fallback for unknown channels
   - Verify fallback for missing metadata

2. **Content extraction tests**
   - YouTube content includes `channel` and `channel_display` fields
   - Non-YouTube content has `channel` = None
   - Metadata without `channel_name` falls back gracefully

3. **Synthesis grouping tests**
   - YouTube content grouped by channel in prompts
   - Channel names appear in synthesis text
   - Weighting still uses "youtube" (0.8x for all channels)

4. **Backwards compatibility tests**
   - Old content without channel metadata still works
   - `sources_included` format unchanged

### UI Tests

1. **Display tests**
   - Channel names displayed in synthesis view
   - Tooltip or context shows it's a YouTube channel
   - Fallback display for unknown channels

2. **Accessibility tests**
   - Screen readers announce channel names correctly

## Definition of Done

- [x] **40.1 Channel Mapping**
  - [x] `YOUTUBE_CHANNEL_DISPLAY` dict in synthesis.py
  - [x] All 4 channels mapped to display names
  - [x] Fallback logic for unknown channels

- [x] **40.2 Content Extraction**
  - [x] `_get_content_for_synthesis()` extracts channel info
  - [x] `channel` and `channel_display` fields added to content items
  - [x] YouTube source type preserved for weighting

- [x] **40.3 Synthesis Prompt**
  - [x] Prompt groups YouTube content by channel name
  - [x] System prompt updated with channel context
  - [x] Weight still shows 0.8x for all YouTube channels

- [x] **40.4 Response Format**
  - [x] Channel attribution visible in synthesis text
  - [x] Backwards compatible with existing `sources_included`

- [x] **40.5 UI Updates**
  - [x] Channel names displayed in synthesis view (dynamic from source_stances)
  - [x] Graceful fallback for missing channel info

- [x] **Tests**
  - [x] Backend tests in `tests/test_prd040_youtube_channels.py` (33 tests)
  - [x] UI tests for channel display
  - [x] All existing tests pass (`pytest` green)

- [x] **Git Workflow**
  - [x] Changes committed to feature branch
  - [x] CLI tests pass
  - [x] Ready for merge to main

## Future Considerations

1. **Additional Channels**: Easy to add new channels by updating `YOUTUBE_CHANNEL_DISPLAY`
2. **Speaker Diarization**: Could identify individual speakers within podcasts (not in scope)
3. **Per-Channel Weighting**: Currently all channels equal; could differentiate in future
4. **Channel Metadata Sync**: Could fetch display names from YouTube API to avoid staleness
