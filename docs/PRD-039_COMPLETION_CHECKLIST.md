# PRD-039 Symbols Feature - Definition of Done

## Overview
This checklist defines explicit completion criteria for fixing the Symbols tab functionality.
All items must be verified before merging to main.

---

## P0: Critical Fixes (Must Pass)

### 1. Frontend Authentication Fix
- [ ] `frontend/js/symbols.js` uses `apiFetch()` instead of `fetch()` for ALL API calls
- [ ] Line ~30: `loadSymbols()` uses `apiFetch('/symbols')`
- [ ] Line ~154: `showSymbolDetail()` uses `apiFetch(`/symbols/${symbolTicker}`)`
- [ ] No raw `fetch()` calls remain in symbols.js
- [ ] **TEST**: Browser console shows no 401 errors when viewing Symbols tab
- [ ] **TEST**: Symbols tab loads without "Failed to load symbols" error (may show empty state)

### 2. Database Persistence in SymbolLevelExtractor
- [ ] New method `save_extraction_to_db(db, extraction_result, content_id)` added
- [ ] Method creates `SymbolLevel` records for each extracted level
- [ ] Method creates/updates `SymbolState` records for each symbol
- [ ] Method links levels to `extracted_from_content_id`
- [ ] Method sets `extraction_method` field correctly
- [ ] Method calls `update_symbol_confluence()` after saving
- [ ] **TEST**: After extraction, `SELECT COUNT(*) FROM symbol_levels` returns > 0
- [ ] **TEST**: After extraction, `SELECT COUNT(*) FROM symbol_states` returns > 0

### 3. Analysis Pipeline Integration
- [ ] `backend/routes/analyze.py` imports `SymbolLevelExtractor`
- [ ] `classify_batch()` calls symbol extraction for KT Technical content
- [ ] `classify_batch()` calls symbol extraction for Discord content
- [ ] Extraction only runs on content types: `blog_post`, `discord_message`, `transcript`
- [ ] Extraction only runs for sources: `kt_technical`, `discord`
- [ ] **TEST**: Running `/api/analyze/classify-batch` on KT content populates symbol tables

### 4. Re-extraction Endpoint
- [ ] New endpoint `POST /api/symbols/extract/{content_id}` exists
- [ ] Endpoint accepts optional `force=true` param to re-extract already-processed content
- [ ] Endpoint returns extraction summary (symbols found, levels created)
- [ ] **TEST**: Calling endpoint on existing KT content creates symbol records

---

## P1: Verification Tests

### Backend Unit Tests
- [ ] All existing PRD-039 tests pass: `pytest tests/test_prd039*.py -v`
- [ ] New test: `test_save_extraction_to_db()` verifies database persistence
- [ ] New test: `test_pipeline_integration()` verifies extraction runs during analysis
- [ ] New test: `test_extract_endpoint()` verifies manual extraction endpoint
- [ ] **COMMAND**: `pytest tests/test_prd039*.py -v` exits with code 0

### API Integration Tests
- [ ] `GET /api/symbols` returns 200 with `symbols` array
- [ ] `GET /api/symbols/GOOGL` returns 200 with symbol detail (or 404 if no data)
- [ ] `GET /api/symbols/GOOGL/levels` returns 200 with `levels` array
- [ ] `POST /api/symbols/extract/{id}` returns 200 with extraction result
- [ ] `POST /api/symbols/refresh` returns 200 and updates staleness
- [ ] **TEST**: All endpoints require authentication (401 without token)

### Playwright UI Tests
- [ ] `tests/playwright/test_symbols_tab.spec.js` tests pass
- [ ] Test: Symbols tab is accessible via navigation
- [ ] Test: Symbol list renders (empty state or with data)
- [ ] Test: No console errors on Symbols tab load
- [ ] Test: Error state shows user-friendly message
- [ ] **COMMAND**: `npx playwright test tests/playwright/test_symbols_tab.spec.js` passes

---

## P2: Code Quality

### No Regressions
- [ ] Existing dashboard functionality works (Overview, Themes, Sources, History tabs)
- [ ] Authentication flow still works (login/logout)
- [ ] Other API endpoints unaffected
- [ ] **TEST**: Manual smoke test of main dashboard features

### Code Standards
- [ ] No hardcoded credentials or API keys
- [ ] Logging added for new functionality
- [ ] Error handling with user-friendly messages
- [ ] No `console.log` debugging statements left in production code

---

## Git Workflow

### Branch Management
- [ ] All work done on feature branch: `claude/debug-symbols-page-G4VCd`
- [ ] Commits have descriptive messages
- [ ] No commits directly to main

### PR Requirements
- [ ] PR created from feature branch to main
- [ ] PR title: "fix(PRD-039): Complete Symbols tab implementation"
- [ ] PR description includes summary of changes
- [ ] All CI tests pass before merge
- [ ] **MERGE CRITERIA**: Only merge when all P0 and P1 items checked

---

## Final Verification Commands

```bash
# 1. Backend tests
pytest tests/test_prd039*.py -v

# 2. Full test suite (ensure no regressions)
pytest tests/ -v --ignore=tests/playwright

# 3. Playwright UI tests
npx playwright test tests/playwright/test_symbols_tab.spec.js

# 4. Manual API verification
curl -X GET "http://localhost:8000/api/symbols" -H "Authorization: Bearer $TOKEN"
```

---

## Sign-off

- [ ] All P0 items complete
- [ ] All P1 items complete
- [ ] All P2 items complete
- [ ] PR merged to main
- [ ] Feature verified working in production (if applicable)

**Date Completed**: _____________
**Verified By**: _____________
