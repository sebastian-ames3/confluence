# PRD-049: System Hardening

**Status**: Not Started
**Priority**: High
**Created**: 2026-01-25
**Source**: Comprehensive system audit

## Overview

This PRD addresses all remaining issues identified during the January 2026 system audit. Critical issues (XSS, missing CSS variables, hardcoded dates, DOM null checks) were fixed immediately. This PRD covers the remaining High, Medium, and Low severity items.

## Background

A comprehensive audit was performed across 6 domains:
1. Synthesis Agent
2. API Routes
3. Frontend JavaScript
4. MCP Tools
5. CSS/Design System
6. Data Models

**Audit Results Summary:**
- 4 Critical issues: FIXED (commit b131fac)
- 7 High severity issues: This PRD
- 21 Medium severity issues: This PRD
- 10 Low severity issues: This PRD

---

## Phase 1: Error Handling & Validation (High Priority)

### 1.1 Silent Validation Failures
**Files:** `agents/synthesis_agent.py`

| Line | Issue | Fix |
|------|-------|-----|
| 1133-1136 | V3 validation returns partial data silently | Log warning, add `validation_passed: false` to response |
| 1344-1352 | V4 source breakdown failures create empty fallbacks | Add `degraded: true` flag when breakdowns fail |
| 791-793 | V2 validation catches all exceptions silently | Log specific errors, return structured error info |
| 1226 | Bare `except:` clause in JSON parsing | Use `except (json.JSONDecodeError, TypeError):` with logging |

### 1.2 API Response Null Safety
**Files:** `backend/routes/synthesis.py`

| Line | Issue | Fix |
|------|-------|-----|
| 615 | `synthesis.synthesis` can be null | Add `or ""` default |
| 619 | `market_regime` can be null | Add `or "unknown"` default |
| 438-440 | Empty list fallback logic ambiguous | Use explicit None checks instead of truthiness |

### 1.3 MCP Tool Error Handling
**Files:** `mcp/server.py`, `mcp/confluence_client.py`

| Location | Issue | Fix |
|----------|-------|-----|
| server.py:632-673 | Symbol tools missing try/catch | Wrap client calls in try/catch, return user-friendly errors |
| server.py:596-629 | Theme tools missing validation | Validate theme_id is not None (not just truthy) |
| server.py:676-682 | Quality tool missing type validation | Convert/validate synthesis_id type |
| confluence_client.py:208-273 | Extract functions return empty on error | Add type validation, return structured error |

**Acceptance Criteria:**
- [ ] All validation failures are logged with context
- [ ] API responses include degradation flags when data is partial
- [ ] MCP tools return helpful error messages instead of crashing
- [ ] No bare `except:` clauses remain

---

## Phase 2: V4 Compatibility (High Priority)

### 2.1 MCP Tier Awareness
**Files:** `mcp/server.py`, `mcp/confluence_client.py`

**Issue:** MCP tools expect Tier 3 data but don't validate what tier was returned.

**Fix:**
1. Add `tier_returned` field to synthesis API response
2. MCP tools check if required fields exist before accessing
3. Return clear error if tool requires data not in current tier

### 2.2 YouTube Channel Format Validation
**Files:** `mcp/confluence_client.py:243-246`

**Issue:** Assumes YouTube channels use `youtube:ChannelName` format without validation.

**Fix:**
1. Add format validation for YouTube channel keys
2. Handle edge cases (missing colon, different naming schemes)
3. Log warnings for unexpected formats

**Acceptance Criteria:**
- [ ] MCP tools gracefully handle Tier 1/2 responses
- [ ] YouTube channel extraction handles all known formats
- [ ] Clear error messages when tier data insufficient

---

## Phase 3: Frontend Resilience (Medium Priority)

### 3.1 Version Detection
**File:** `frontend/index.html:737-738`

**Issue:** Version detection relies on property presence, not explicit version field.

**Current:**
```javascript
const isV4 = data.version === '4.0' || data.source_breakdowns;
const isV3 = isV4 || data.version === '3.0' || data.confluence_zones;
```

**Fix:**
```javascript
const version = String(data.version || '1.0');
const isV4 = version.startsWith('4');
const isV3 = version.startsWith('3') || version.startsWith('4');
```

### 3.2 Tier Button State Bug
**File:** `frontend/index.html:712`

**Issue:** On error, button text shows new tier instead of reverting to previous.

**Fix:** Store original tier before update, restore on error.

### 3.3 Incomplete Optional Chaining
**File:** `frontend/index.html:1118,1122`

**Issue:** `?.view` returns "undefined" string instead of fallback.

**Fix:** Use `?? '-'` instead of `|| '-'`

### 3.4 SVG Gradient ID Collisions
**File:** `frontend/index.html:898,1161`

**Issue:** V3 and V4 sparkline gradients could conflict.

**Fix:** Use unique prefix per function (`sparkline-v4-${index}` vs `sparkline-v3-${index}`)

**Acceptance Criteria:**
- [ ] Version detection is explicit and robust
- [ ] Tier selector maintains correct state on errors
- [ ] Optional chaining uses nullish coalescing
- [ ] No SVG gradient ID conflicts

---

## Phase 4: CSS & Responsive (Medium Priority)

### 4.1 Fixed Max-Height
**File:** `frontend/css/components/_cards.css:680`

**Issue:** `max-height: 500px` is hardcoded, no responsive variants.

**Fix:**
```css
.source-perspective-card.expanded .source-perspective-details {
  max-height: 400px;
}
@media (min-width: 768px) {
  .source-perspective-card.expanded .source-perspective-details {
    max-height: 500px;
  }
}
@media (min-width: 1200px) {
  .source-perspective-card.expanded .source-perspective-details {
    max-height: 600px;
  }
}
```

### 4.2 Breakpoint Alignment
**File:** `frontend/css/components/_cards.css:780`

**Issue:** Uses 1200px instead of defined breakpoints (1024px or 1280px).

**Fix:** Change to `@media (max-width: 1280px)` to align with `--breakpoint-xl`.

### 4.3 Animation Timing Mismatch
**File:** `frontend/css/components/_cards.css:665-676`

**Issue:** Icon transition (250ms) vs panel transition (400ms) creates jank.

**Fix:** Sync both to `var(--transition-normal)` (250ms).

### 4.4 Firefox Scrollbar Support
**File:** `frontend/css/components/_cards.css:685-701`

**Issue:** No Firefox scrollbar styling fallback.

**Fix:**
```css
@supports (scrollbar-width: thin) {
  .source-perspective-card.expanded .source-perspective-details {
    scrollbar-width: thin;
    scrollbar-color: var(--border-medium) var(--glass-bg-light);
  }
}
```

**Acceptance Criteria:**
- [ ] Expanded card heights adapt to viewport
- [ ] Breakpoints use design system variables
- [ ] Animations are synchronized
- [ ] Firefox has styled scrollbars

---

## Phase 5: Backend Improvements (Medium Priority)

### 5.1 Datetime Consistency
**File:** `agents/synthesis_agent.py:1118`

**Issue:** V1 timestamps have "Z" suffix, V3/V4 don't.

**Fix:** Add "Z" suffix to all `datetime.utcnow().isoformat()` calls.

### 5.2 Version Parameter Validation
**File:** `backend/routes/synthesis.py`

**Issue:** Invalid versions silently default to V1.

**Fix:** Add explicit validation, return 400 for invalid versions.

### 5.3 Token Usage Field
**File:** `backend/models.py:344`

**Issue:** `token_usage` field defined but never populated.

**Decision:** Either populate from Claude API response or remove field.

### 5.4 YouTube Channels Indexing
**File:** `backend/models.py`

**Issue:** YouTube channels stored in JSON only, can't query directly.

**Fix:** Add `youtube_channels` Text column for V4 metadata.

**Acceptance Criteria:**
- [ ] All timestamps are UTC with Z suffix
- [ ] Invalid API parameters return 400 errors
- [ ] Token usage tracked or field removed
- [ ] YouTube channels queryable

---

## Phase 6: Low Priority Improvements

### 6.1 Regex Pattern Refinement
**File:** `agents/synthesis_agent.py:478,482,493`

**Issue:** Price/VIX/option extraction patterns are too broad.

**Fix:** Add boundary conditions, test cases for edge cases.

### 6.2 Source-Specific Prompts
**File:** `agents/synthesis_agent.py:1339`

**Issue:** V4 breakdowns use generic prompt for all sources.

**Fix:** Tailor prompts per source type (options flow vs macro research vs technical).

### 6.3 MCP Logging
**File:** `mcp/server.py`

**Issue:** No logging in tool handlers.

**Fix:** Add structured logging with tool name, arguments, timing.

### 6.4 Search Endpoint Documentation
**File:** `mcp/confluence_client.py:72`

**Issue:** Uses `/api/synthesis/debug` which isn't documented.

**Fix:** Either document endpoint or create dedicated search endpoint.

### 6.5 Database Constraints
**File:** `backend/models.py`

**Issue:** No CHECK constraints on market_regime and schema_version.

**Fix:** Add constraints for data integrity.

**Acceptance Criteria:**
- [ ] Regex patterns have test coverage
- [ ] Source-specific prompts improve breakdown quality
- [ ] MCP operations are logged
- [ ] All API endpoints are documented
- [ ] Database has appropriate constraints

---

## Testing Requirements

### Unit Tests
- [ ] Validation failure scenarios return structured errors
- [ ] MCP tools handle missing tier data gracefully
- [ ] Version detection works for all valid versions
- [ ] CSS variables all resolve correctly

### Integration Tests
- [ ] End-to-end synthesis flow with degraded data
- [ ] MCP tools with Tier 1/2/3 responses
- [ ] Frontend handles all API response variations

### Manual Testing
- [ ] Visual inspection of responsive breakpoints
- [ ] Animation smoothness across browsers
- [ ] Firefox scrollbar appearance

---

## Implementation Order

1. **Week 1:** Phase 1 (Error Handling) + Phase 2 (V4 Compatibility)
2. **Week 2:** Phase 3 (Frontend) + Phase 4 (CSS)
3. **Week 3:** Phase 5 (Backend) + Phase 6 (Low Priority)

---

## Success Metrics

- Zero silent failures in production logs
- All MCP tools return actionable responses
- No console errors on dashboard load
- Cross-browser visual consistency
- 100% test coverage on new validation code

---

## Files Affected

| File | Phases |
|------|--------|
| `agents/synthesis_agent.py` | 1, 5, 6 |
| `backend/routes/synthesis.py` | 1, 5 |
| `backend/models.py` | 5 |
| `mcp/server.py` | 1, 2, 6 |
| `mcp/confluence_client.py` | 1, 2 |
| `frontend/index.html` | 3 |
| `frontend/css/components/_cards.css` | 4 |
