# Changelog

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

## PRD Completion Status

| PRD | Status |
|-----|--------|
| 001-011 | Complete |
| 012 | Complete |
| 013 | Complete |
| 014 | Complete |
| 015 | Complete |
| 016 | Complete |
| 017 | Complete |
| 018 | Not started |

---

**Last Updated**: 2025-12-03
