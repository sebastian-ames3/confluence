# PRD-033: Sources & History Tab Implementation

## Overview

Implement the Sources and History tabs in the dashboard, connecting existing backend APIs to the frontend UI. Both tabs currently show placeholder text despite fully functional API endpoints existing.

## Problem Statement

The dashboard has four tabs: Overview, Themes, Sources, and History. While Overview and Themes are functional, Sources and History display static placeholder text:
- **Sources tab**: Shows "Loading source details..." but never loads
- **History tab**: Shows "Coming soon..." but the API exists

This creates an incomplete user experience and wastes existing backend functionality.

## Existing Infrastructure

### Available API Endpoints

| Endpoint | Method | Purpose | Response Shape |
|----------|--------|---------|----------------|
| `/api/dashboard/sources` | GET | List all sources with stats | `[{id, name, type, active, total_items, analyzed_items, last_collected}]` |
| `/api/dashboard/sources/{name}` | GET | Get source content with pagination | `[{id, title, collected_at, content_type, analysis}]` |
| `/api/collect/stats/{name}` | GET | Detailed source statistics | `{source, type, content_by_type, recent_collections}` |
| `/api/synthesis/history` | GET | Synthesis history with pagination | `{syntheses: [{id, preview, themes, time_window, market_regime, generated_at}], total, limit, offset}` |
| `/api/synthesis/{id}` | GET | Full synthesis by ID | Full synthesis object with all fields |
| `/api/synthesis/status/collections` | GET | Collection run history | `{collection_runs: [{id, run_type, started_at, status, total_items, errors}]}` |

### Current Frontend State

```javascript
// Sources Tab - Line 369-379 of index.html
<div class="tab-panel" id="panel-sources">
    <div id="sources-detail-list">
        <p>Loading source details...</p>  // Never populated
    </div>
</div>

// History Tab - Line 381-391 of index.html
<div class="tab-panel" id="panel-history">
    <div id="synthesis-history-list">
        <p>Coming soon...</p>  // Static text
    </div>
</div>
```

---

## Data Flow Specifications

### Sources Tab Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        SOURCES TAB                               │
└─────────────────────────────────────────────────────────────────┘

User clicks "Sources" tab
         │
         ▼
┌─────────────────┐     GET /api/dashboard/sources     ┌──────────────────┐
│   Frontend      │ ─────────────────────────────────► │   Backend        │
│   loadSources() │                                     │   dashboard.py   │
└─────────────────┘                                     └──────────────────┘
         │                                                       │
         │                                                       ▼
         │                                              ┌──────────────────┐
         │                                              │   Database       │
         │                                              │   - Source       │
         │                                              │   - RawContent   │
         │                                              │   - Analyzed     │
         │                                              └──────────────────┘
         │                                                       │
         │                    Response 200                       │
         │ ◄─────────────────────────────────────────────────────┘
         │   [{id, name, type, active, total_items,
         │     analyzed_items, last_collected}]
         ▼
┌─────────────────┐
│ displaySources()│
│ - Source cards  │
│ - Stats badges  │
│ - Last updated  │
└─────────────────┘
         │
         │  User clicks source card
         ▼
┌─────────────────┐  GET /api/dashboard/sources/{name}  ┌──────────────────┐
│ loadSourceDetail│ ──────────────────────────────────► │   Backend        │
│ (source_name)   │        ?limit=20&offset=0           │                  │
└─────────────────┘                                     └──────────────────┘
         │                                                       │
         │                    Response 200                       │
         │ ◄─────────────────────────────────────────────────────┘
         │   [{id, title, collected_at, content_type,
         │     summary, sentiment, themes}]
         ▼
┌─────────────────┐
│displaySourceDetail│
│ - Content list  │
│ - Pagination    │
│ - Back button   │
└─────────────────┘
```

### History Tab Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        HISTORY TAB                               │
└─────────────────────────────────────────────────────────────────┘

User clicks "History" tab
         │
         ▼
┌─────────────────┐    GET /api/synthesis/history      ┌──────────────────┐
│   Frontend      │ ─────────────────────────────────► │   Backend        │
│   loadHistory() │       ?limit=10&offset=0           │   synthesis.py   │
└─────────────────┘                                     └──────────────────┘
         │                                                       │
         │                    Response 200                       │
         │ ◄─────────────────────────────────────────────────────┘
         │   {syntheses: [...], total, limit, offset}
         ▼
┌─────────────────┐
│ displayHistory()│
│ - Synthesis cards│
│ - Date/time     │
│ - Market regime │
│ - Theme badges  │
└─────────────────┘
         │
         │  User clicks synthesis card
         ▼
┌─────────────────┐    GET /api/synthesis/{id}         ┌──────────────────┐
│loadSynthesisDetail│ ────────────────────────────────►│   Backend        │
│ (synthesis_id)  │                                     │                  │
└─────────────────┘                                     └──────────────────┘
         │                                                       │
         │                    Response 200                       │
         │ ◄─────────────────────────────────────────────────────┘
         │   {id, synthesis, key_themes, market_regime,
         │    high_conviction_ideas, catalysts, ...}
         ▼
┌─────────────────┐
│displaySynthesisDetail│
│ - Full synthesis│
│ - Themes list   │
│ - Ideas list    │
│ - Back button   │
└─────────────────┘
```

---

## Implementation Specification

### Phase 1: Sources Tab

#### 1.1 Sources List View

**JavaScript Functions to Add:**

```javascript
// Load all sources
async function loadSources() {
    const response = await fetch(`${API_BASE}/dashboard/sources`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const sources = await response.json();
    displaySources(sources);
}

// Display sources list
function displaySources(sources) {
    const container = document.getElementById('sources-detail-list');
    // Render source cards with: name, type, total_items, analyzed_items, last_collected
}

// Load source detail (content list)
async function loadSourceDetail(sourceName) {
    const response = await fetch(`${API_BASE}/dashboard/sources/${sourceName}?limit=20`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const content = await response.json();
    displaySourceDetail(sourceName, content);
}
```

**UI Components:**
- Source card grid (reuse `.sidebar-card` styling)
- Stats row: Total items | Analyzed | Last collected
- Status indicator: Active (green) / Inactive (gray)
- Click handler to drill into source content

#### 1.2 Source Detail View

**UI Components:**
- Back button to return to sources list
- Source header with name and stats
- Content list with: title, date, type badge, sentiment indicator
- Pagination controls (Next/Previous)

### Phase 2: History Tab

#### 2.1 Synthesis History List

**JavaScript Functions to Add:**

```javascript
// Load synthesis history
async function loadHistory(offset = 0) {
    const response = await fetch(`${API_BASE}/synthesis/history?limit=10&offset=${offset}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    displayHistory(data);
}

// Display history list
function displayHistory(data) {
    const container = document.getElementById('synthesis-history-list');
    // Render synthesis cards with: date, time_window, market_regime, themes preview
}
```

**UI Components:**
- Synthesis card list (chronological, newest first)
- Each card shows: Generated date/time, Time window badge, Market regime badge, Theme tags (max 3)
- Preview text (first 100 chars of synthesis)
- Pagination controls

#### 2.2 Synthesis Detail View

**JavaScript Functions to Add:**

```javascript
// Load full synthesis
async function loadSynthesisDetail(synthesisId) {
    const response = await fetch(`${API_BASE}/synthesis/${synthesisId}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const synthesis = await response.json();
    displaySynthesisDetail(synthesis);
}
```

**UI Components:**
- Back button to return to history list
- Full synthesis text
- Key themes list
- High conviction ideas
- Contradictions
- Catalysts

### Phase 3: Tab Event Wiring

Update tab change handler to load data:

```javascript
window.addEventListener('tabchange', (e) => {
    if (e.detail.tab === 'themes') {
        loadThemes();
    } else if (e.detail.tab === 'sources') {
        loadSources();
    } else if (e.detail.tab === 'history') {
        loadHistory();
    }
});
```

---

## Integration Tests

### Test File: `tests/test_sources_history_integration.py`

```python
"""
Integration tests for Sources and History tab functionality.
Tests the full data flow from API to expected response shapes.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)
AUTH = ("sames3", "Spotswood1")


class TestSourcesAPIIntegration:
    """Test Sources tab API endpoints return valid data."""

    def test_get_sources_returns_200(self):
        """GET /api/dashboard/sources returns 200."""
        response = client.get("/api/dashboard/sources", auth=AUTH)
        assert response.status_code == 200

    def test_get_sources_returns_list(self):
        """Response is a list of source objects."""
        response = client.get("/api/dashboard/sources", auth=AUTH)
        data = response.json()
        assert isinstance(data, list)

    def test_source_object_has_required_fields(self):
        """Each source has required fields for UI rendering."""
        response = client.get("/api/dashboard/sources", auth=AUTH)
        data = response.json()
        if len(data) > 0:
            source = data[0]
            required_fields = ["id", "name", "type", "active", "total_items"]
            for field in required_fields:
                assert field in source, f"Missing field: {field}"

    def test_get_source_detail_returns_200(self):
        """GET /api/dashboard/sources/{name} returns 200 for valid source."""
        # First get a valid source name
        sources = client.get("/api/dashboard/sources", auth=AUTH).json()
        if len(sources) > 0:
            source_name = sources[0]["name"]
            response = client.get(f"/api/dashboard/sources/{source_name}", auth=AUTH)
            assert response.status_code == 200

    def test_get_source_stats_returns_200(self):
        """GET /api/collect/stats/{name} returns 200."""
        sources = client.get("/api/dashboard/sources", auth=AUTH).json()
        if len(sources) > 0:
            source_name = sources[0]["name"]
            response = client.get(f"/api/collect/stats/{source_name}", auth=AUTH)
            assert response.status_code == 200


class TestHistoryAPIIntegration:
    """Test History tab API endpoints return valid data."""

    def test_get_synthesis_history_returns_200(self):
        """GET /api/synthesis/history returns 200."""
        response = client.get("/api/synthesis/history", auth=AUTH)
        assert response.status_code == 200

    def test_synthesis_history_has_required_structure(self):
        """Response has syntheses array and pagination fields."""
        response = client.get("/api/synthesis/history", auth=AUTH)
        data = response.json()
        assert "syntheses" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["syntheses"], list)

    def test_synthesis_object_has_required_fields(self):
        """Each synthesis has required fields for UI rendering."""
        response = client.get("/api/synthesis/history", auth=AUTH)
        data = response.json()
        if len(data["syntheses"]) > 0:
            synthesis = data["syntheses"][0]
            required_fields = ["id", "time_window", "generated_at"]
            for field in required_fields:
                assert field in synthesis, f"Missing field: {field}"

    def test_get_synthesis_by_id_returns_200(self):
        """GET /api/synthesis/{id} returns 200 for valid ID."""
        history = client.get("/api/synthesis/history", auth=AUTH).json()
        if len(history["syntheses"]) > 0:
            synth_id = history["syntheses"][0]["id"]
            response = client.get(f"/api/synthesis/{synth_id}", auth=AUTH)
            assert response.status_code == 200

    def test_collection_history_returns_200(self):
        """GET /api/synthesis/status/collections returns 200."""
        response = client.get("/api/synthesis/status/collections", auth=AUTH)
        assert response.status_code == 200


class TestDataAvailability:
    """Test that real data exists for UI population."""

    def test_sources_exist(self):
        """At least one source exists in the system."""
        response = client.get("/api/dashboard/sources", auth=AUTH)
        data = response.json()
        assert len(data) > 0, "No sources found - UI will show empty state"

    def test_source_has_content(self):
        """At least one source has collected content."""
        response = client.get("/api/dashboard/sources", auth=AUTH)
        sources = response.json()
        has_content = any(s["total_items"] > 0 for s in sources)
        assert has_content, "No source has content - Sources tab will be empty"

    def test_synthesis_history_not_empty(self):
        """At least one synthesis exists for history tab."""
        response = client.get("/api/synthesis/history", auth=AUTH)
        data = response.json()
        assert data["total"] > 0, "No syntheses found - History tab will be empty"
```

---

## Acceptance Criteria

### Sources Tab

| # | Criterion | Validation Method |
|---|-----------|-------------------|
| S1 | `GET /api/dashboard/sources` returns HTTP 200 | Integration test |
| S2 | Sources list displays all active sources | Manual verification |
| S3 | Each source card shows: name, type, total items, last collected date | Manual verification |
| S4 | Clicking a source card loads its content via `GET /api/dashboard/sources/{name}` | Network inspector |
| S5 | Source detail view shows content items with title, date, type | Manual verification |
| S6 | Back button returns to sources list without page reload | Manual verification |
| S7 | Empty state shown if source has no content | Manual verification |
| S8 | Error state shown if API call fails (4xx/5xx) | Force error, verify UI |

### History Tab

| # | Criterion | Validation Method |
|---|-----------|-------------------|
| H1 | `GET /api/synthesis/history` returns HTTP 200 | Integration test |
| H2 | History list displays past syntheses in reverse chronological order | Manual verification |
| H3 | Each synthesis card shows: date, time window, market regime, themes | Manual verification |
| H4 | Clicking a synthesis loads full detail via `GET /api/synthesis/{id}` | Network inspector |
| H5 | Synthesis detail shows full text, themes, ideas, contradictions | Manual verification |
| H6 | Back button returns to history list without page reload | Manual verification |
| H7 | Pagination works (Next/Previous or infinite scroll) | Manual verification |
| H8 | Empty state shown if no syntheses exist | Manual verification |
| H9 | Error state shown if API call fails (4xx/5xx) | Force error, verify UI |

### General

| # | Criterion | Validation Method |
|---|-----------|-------------------|
| G1 | Tab switching loads data for that tab (lazy loading) | Network inspector |
| G2 | Loading state shown while fetching data | Manual verification |
| G3 | All API calls include authentication | Network inspector |
| G4 | No console errors during normal operation | Browser console |
| G5 | All integration tests pass | `pytest tests/test_sources_history_integration.py` |

---

## Definition of Done

### Pre-Implementation Checklist

- [ ] PRD reviewed and approved by stakeholder
- [ ] All existing API endpoints verified working (manual curl tests)
- [ ] Integration test file created and baseline tests pass

### Implementation Checklist

- [ ] **Sources Tab - List View**
  - [ ] `loadSources()` function implemented
  - [ ] `displaySources()` function implemented
  - [ ] Source cards render with all required data
  - [ ] Active/inactive status indicator works

- [ ] **Sources Tab - Detail View**
  - [ ] `loadSourceDetail()` function implemented
  - [ ] `displaySourceDetail()` function implemented
  - [ ] Back button returns to list view
  - [ ] Pagination controls work (if >20 items)

- [ ] **History Tab - List View**
  - [ ] `loadHistory()` function implemented
  - [ ] `displayHistory()` function implemented
  - [ ] Synthesis cards render with all required data
  - [ ] Market regime badge colors correct
  - [ ] Theme tags display (max 3-5)

- [ ] **History Tab - Detail View**
  - [ ] `loadSynthesisDetail()` function implemented
  - [ ] `displaySynthesisDetail()` function implemented
  - [ ] Full synthesis text renders
  - [ ] Back button returns to list view

- [ ] **Tab Wiring**
  - [ ] Tab change event triggers correct load function
  - [ ] Data only loads on first tab visit (not on every switch)

- [ ] **Error Handling**
  - [ ] Loading states display during fetch
  - [ ] Error states display on API failure
  - [ ] Empty states display when no data

### Testing Checklist

- [ ] All integration tests pass: `pytest tests/test_sources_history_integration.py -v`
- [ ] All existing tests still pass: `pytest tests/ -v`
- [ ] Manual testing completed for all acceptance criteria
- [ ] No console errors in browser during testing

### API Verification Checklist

| Endpoint | Status | Notes |
|----------|--------|-------|
| `GET /api/dashboard/sources` | ⬜ | |
| `GET /api/dashboard/sources/{name}` | ⬜ | |
| `GET /api/collect/stats/{name}` | ⬜ | |
| `GET /api/synthesis/history` | ⬜ | |
| `GET /api/synthesis/{id}` | ⬜ | |
| `GET /api/synthesis/status/collections` | ⬜ | |

### UI Verification Checklist

| View | Shows Real Data | Notes |
|------|-----------------|-------|
| Sources list | ⬜ | |
| Source detail | ⬜ | |
| History list | ⬜ | |
| Synthesis detail | ⬜ | |

### Final Checklist

- [ ] Feature branch created: `feature/prd-033-sources-history-tabs`
- [ ] All code committed with descriptive messages
- [ ] PR created with test results
- [ ] CI tests pass
- [ ] PR merged to main
- [ ] Deployed to production (Railway auto-deploy)
- [ ] Production verification completed
- [ ] PRD moved to `/docs/archived/`

---

## Out of Scope

- Collection triggering from Sources tab (use existing Quick Actions)
- Synthesis regeneration from History tab (use existing FAB buttons)
- Real-time updates / WebSocket integration
- Export functionality (PDF/CSV)
- Search/filter within tabs

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| No data in database | Empty tabs | Run collection + synthesis before testing |
| API rate limiting | Slow tab loads | Implement caching / debounce rapid switches |
| Large datasets | Performance issues | Pagination with reasonable limits (10-20 items) |

---

## Timeline

| Phase | Effort |
|-------|--------|
| Phase 1: Sources Tab | ~2 hours |
| Phase 2: History Tab | ~2 hours |
| Phase 3: Testing & Polish | ~1 hour |
| **Total** | ~5 hours |

---

## Appendix: API Response Examples

### GET /api/dashboard/sources
```json
[
  {
    "id": 1,
    "name": "Discord",
    "type": "discord",
    "active": true,
    "total_items": 1250,
    "analyzed_items": 1180,
    "last_collected": "2025-12-11T14:30:00Z"
  },
  {
    "id": 2,
    "name": "42 Macro",
    "type": "macro",
    "active": true,
    "total_items": 45,
    "analyzed_items": 45,
    "last_collected": "2025-12-10T09:00:00Z"
  }
]
```

### GET /api/synthesis/history
```json
{
  "syntheses": [
    {
      "id": 15,
      "synthesis_preview": "Market sentiment remains cautious ahead of FOMC...",
      "key_themes": ["FOMC hawkish cut", "Vol expansion"],
      "time_window": "7d",
      "content_count": 87,
      "market_regime": "risk-off",
      "generated_at": "2025-12-11T12:00:00Z"
    }
  ],
  "total": 15,
  "limit": 10,
  "offset": 0
}
```
