# Changelog

## [1.7.1] - 2025-12-10

### Changed
- **Dashboard Layout Restructure** - Above-the-fold optimization
  - Moved Market Visualization charts to top of Overview tab (2x2 grid layout)
  - Created new "Key Takeaways" compact card (max 5 bullets, replaces verbose synthesis)
  - Added "View Full Synthesis" collapsible panel (hidden by default)
  - Reordered sections: Charts → Takeaways → Focus → Confluence → Conflicts → Full Synthesis
  - Made Source Perspectives sidebar scrollable (`max-height: 400px`)

- **CSS Updates**
  - `.charts-grid`: Changed to `repeat(2, 1fr)` for 2x2 layout
  - `.chart-container-md`: Updated to `min-height: 180px; height: auto`

- **JavaScript Updates**
  - Added `toggleFullSynthesis()` function to show/hide synthesis panel
  - Updated `displaySynthesis()` to populate Key Takeaways list (from `key_takeaways` or fallback sentences)
  - Updated `showEmptySynthesis()` to handle new takeaways section

---

## [1.7.0] - 2025-12-10

### Added
- **[PRD-026 to PRD-032] UI/UX Modernization** - Complete with Playwright Tests
  - **PRD-026**: Modern UI design with glassmorphism, 3D card tilt, animated counters
  - **PRD-027**: Design system foundation with all tokens (colors, typography, spacing, shadows, gradients)
  - **PRD-028**: Component library (buttons, cards, badges, inputs, tabs, tables, tooltips, progress, loaders, toasts, modals)
  - **PRD-029**: Layout & navigation system with responsive grid
  - **PRD-030**: Animations & microinteractions (page transitions, loading states, skeleton loaders, easing functions)
  - **PRD-031**: Data visualization with Chart.js (radar, donut, timeline, gauge, bar, heatmap)
  - **PRD-032**: Accessibility & performance (WCAG 2.1 AA, ARIA live regions, Web Vitals, lazy loading, caching)

- **124 Playwright Tests** for frontend UI verification
  - 26 tests for PRD-026 (glassmorphism, animations)
  - 20 tests for PRD-027 (design tokens)
  - 13 tests for PRD-028 (components)
  - 3 tests for PRD-029 (layout)
  - 19 tests for PRD-030 (animations)
  - 21 tests for PRD-031 (charts)
  - 22 tests for PRD-032 (accessibility/performance)

### Changed
- `frontend/css/main.css` - Added all CSS module imports
- `frontend/index.html` - Added Chart.js CDN and all chart scripts
- `frontend/css/design-system/_effects.css` - Added easing CSS variables

---

## [1.6.0] - 2025-12-07

### Added
- **[PRD-024] Theme Tracking System** - Complete
  - PRD created: structured theme tracking with source-level evidence
  - Theme lifecycle: emerging → active → evolved → dormant
  - Claude-based semantic matching for theme consolidation
  - Per-source evidence tracking without pseudo-Bayesian scores

- **[PRD-025] Enhanced Synthesis Summary** - Complete
  - Updated v3 synthesis prompt with comprehensive executive_summary
  - Added: macro_context, source_highlights, synthesis_narrative, key_takeaways
  - Increased max_tokens from 4000→5000 for expanded output

### Changed
- `agents/synthesis_agent.py` - Enhanced executive_summary schema for v3
- `CLAUDE.md` - Updated with PRD-024/025 status

---

## [1.5.0] - 2025-12-06

### Added
- Manual collection trigger buttons on dashboard (YouTube, Substack, KT Technical)
- Migration 005: schema_version and synthesis_json columns for v2/v3 persistence

### Fixed
- KT Technical image analysis: Added "blog_post" to classifier ROUTING_MAP
- 42 Macro PDF analysis: Added run_pdf_analysis execution to analyze.py
- 42 Macro local PDFs: Extract text via PyPDF2 before Railway upload
- Video transcripts: Create AnalyzedContent records after transcription

---

## [1.4.0] - 2025-12-03

### Added
- **[PRD-018] Video Transcription** - Complete
  - Wired `TranscriptHarvesterAgent` into collection endpoints
  - `/api/collect/discord` triggers async transcription for videos without local transcripts
  - `/api/collect/42macro` triggers async transcription for all video content
  - Added `_transcribe_video_sync()` and `_transcribe_video_async()` to collect.py
  - Uses ThreadPoolExecutor (2 workers) to avoid blocking collection
  - Transcripts stored in `content_text` and `json_metadata.transcript`
  - API responses include `transcription_queued` count

### Changed
- Discord ingestion checks for existing local transcripts before queuing server-side transcription
- 42 Macro videos (Vimeo) now automatically transcribed after collection

---

## [1.3.0] - 2025-12-03

### Added
- **[PRD-019] Duplicate Detection** - Complete
  - Created `backend/utils/deduplication.py` with `check_duplicate()` utility
  - All collection endpoints now check for duplicates before saving
  - Added database indexes for efficient duplicate lookups
  - API responses include `skipped_duplicates` count

- **42 Macro Video Collection**
  - Fixed video menu item detection on `/video/around_the_horn_weekly`
  - Scrolls through ATH menu items to capture all videos
  - Extracts Vimeo video IDs for transcription pipeline

### Changed
- `/api/collect/discord` - Now skips duplicate messages (by message_id)
- `/api/collect/42macro` - Now skips duplicate items (by URL, video_id, or report_type+date)
- `_save_collected_items()` in trigger.py - Returns save/skip counts
- RawContent model - Added composite indexes on (source_id, url) and (source_id, content_type)

### Fixed
- Unicode emoji logging errors on Windows (replaced with ASCII text)

---

## [1.2.0] - 2025-12-03

### Added
- **[PRD-017] Polish & Reliability** - Complete
  - Fixed synthesis endpoint slowapi request parameter naming conflict
  - Added global exception handler for better error visibility
  - Added `/api/synthesis/debug` endpoint for pipeline diagnostics
  - Discord collector now properly uploads to Railway via `--railway-api`

### Fixed
- Synthesis generation 500 error (slowapi required `request` parameter name)
- Discord collector datetime parsing (added python-dateutil)
- Analysis router registration in app.py
- Synthesis query to include NULL analyzed_at values

### Working Pipeline (tested Dec 3)
1. Discord collection → 40 messages uploaded to Railway
2. Content analysis → 40 items classified
3. Synthesis generation → First synthesis saved (ID: 1)

---

## [1.1.0] - 2025-12-02

### Added
- **[PRD-016] MCP Server API Proxy Refactor** - Complete
  - MCP server fetches data via HTTP API (not direct SQLite)
  - Enables Claude Desktop to access Railway production data
  - New search endpoints: `/api/search/content`, `/api/search/themes/aggregated`

- **[PRD-015] Security Hardening** - Complete
  - HTTP Basic Auth on all API routes (except /health)
  - Rate limiting with slowapi
  - Discord channel IDs in environment variables

---

## [1.0.0] - 2025-11-30

### Added
- **[PRD-013] MCP Server** - 5 tools for Claude Desktop
- **[PRD-014] Deployment** - Railway configuration
- **Confluence Routes** - Full REST API for scoring

---

## [0.9.0] - 2025-11-20

### Added
- **[PRD-004] Discord Collector** - Local collection with discord.py-self
- **[PRD-003] Content Classifier** - AI routing agent

---

## PRD Status

| PRD | Status |
|-----|--------|
| 001-032 | Complete |

---

**Last Updated**: 2025-12-10
