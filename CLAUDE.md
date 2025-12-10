# Macro Confluence Hub

Personal investment research aggregation system. Collects from 5 sources, applies AI analysis, surfaces confluence via web dashboard and Claude Desktop MCP.

**Version**: 1.6.0 (Dec 2025) | **Status**: Production

---

## Quick Reference

### Generate New v3 Synthesis
```bash
curl -X POST -u sames3:Spotswood1 -H "Content-Type: application/json" \
  -d '{"time_window": "7d", "version": "3"}' \
  https://confluence-production-a32e.up.railway.app/api/synthesis/generate
```

### Run Discord Collection (local)
```bash
cd "C:\Users\14102\Documents\Sebastian Ames\Projects\Confluence"
python dev/scripts/discord_local.py --railway-api
```

### Run 42 Macro Collection (local)
```bash
python dev/scripts/macro42_local.py --railway-api
```

### Trigger Analysis Pipeline
```bash
curl -X POST -u sames3:Spotswood1 \
  https://confluence-production-a32e.up.railway.app/api/analyze/classify-batch
```

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Collectors │────▶│   Backend   │────▶│  Dashboard  │
│  (Local)    │     │  (Railway)  │     │  (Railway)  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ MCP Server  │
                    │(Claude Desktop)│
                    └─────────────┘
```

### Data Flow
1. **Collect**: Local scripts upload to Railway API
2. **Analyze**: `/api/analyze/classify-batch` runs AI analysis
3. **Synthesize**: `/api/synthesis/generate` creates v3 research summary
4. **View**: Dashboard at Railway URL or query via MCP tools

---

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `/agents/` | 10 AI agents (synthesis, scoring, analysis) |
| `/backend/` | FastAPI app, routes, models |
| `/collectors/` | Source-specific collection logic |
| `/frontend/` | Dashboard (vanilla JS + Chart.js) |
| `/mcp/` | Claude Desktop MCP server |
| `/dev/scripts/` | Local collection scripts |
| `/tests/` | Unit tests |
| `/docs/archived/` | Completed PRDs |

---

## Data Sources

| Source | Type | Collection Method |
|--------|------|-------------------|
| Discord (Options Insight) | Real-time trades | discord.py-self (local) |
| 42 Macro | Institutional research | Selenium (local) |
| KT Technical | Elliott Wave analysis | Session auth |
| YouTube | Macro commentary | API v3 |
| Substack | Thematic research | RSS |

---

## API Endpoints (Key)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/synthesis/generate` | POST | Generate v1/v2/v3 synthesis |
| `/api/synthesis/latest` | GET | Get most recent synthesis |
| `/api/analyze/classify-batch` | POST | Run analysis on unprocessed content |
| `/api/collect/discord` | POST | Upload Discord content |
| `/api/dashboard/today` | GET | Dashboard summary data |

---

## MCP Tools (Claude Desktop)

| Tool | Purpose |
|------|---------|
| `get_latest_synthesis` | Full v3 synthesis |
| `get_executive_summary` | Quick overview |
| `get_confluence_zones` | Where sources align |
| `get_conflicts` | Where sources disagree |
| `get_attention_priorities` | Ranked focus areas |
| `get_source_stance` | Specific source view |
| `get_catalyst_calendar` | Upcoming events |
| `search_research` | Search content |
| `get_themes` | All tracked themes (with status filter) |
| `get_active_themes` | Currently active themes |
| `get_theme_detail` | Deep-dive into specific theme |
| `get_themes_summary` | Theme tracking stats |

---

## Environment

- **Production**: Railway (https://confluence-production-a32e.up.railway.app)
- **Auth**: HTTP Basic (`sames3` / `Spotswood1`)
- **Database**: SQLite on Railway volume
- **AI**: Claude Sonnet 4, Whisper API

---

## PRDs

| PRD | Feature | Status |
|-----|---------|--------|
| 001-017 | Foundation, agents, dashboard, deployment, security | Complete |
| 018 | Video Transcription (Whisper + Claude analysis) | Complete |
| 019 | Duplicate Detection (deduplication across collectors) | Complete |
| 020 | Actionable Synthesis V2 (levels, conviction, entry/stop/target) | Complete |
| 021 | Research Consumption Hub V3 (confluence zones, conflict watch) | Complete |
| 022 | MCP Server (Claude Desktop SSE/stdio integration) | Complete |
| 023 | Final Cleanup (archive scripts, consolidate docs) | Complete |
| 024 | Theme Tracking System | Complete |
| 025 | Enhanced Synthesis Summary | Complete |
| 026-032 | UI/UX Modernization | Complete |

**018**: `agents/transcript_harvester.py` - yt-dlp download, Whisper transcription, Claude analysis with priority tiers
**019**: `backend/utils/deduplication.py` - check_duplicate() used in collect.py and trigger.py endpoints
**020**: Synthesis V2 with specific prices/strikes, weighted conviction scoring, trade structures
**021**: Synthesis V3 with confluence_zones, conflict_watch, attention_priorities, re_review_recommendations
**022**: `mcp/server.py` - 12 tools for Claude Desktop, SSE and stdio modes
**024**: Theme tracking with source-level evidence, lifecycle (emerging→active→evolved→dormant), MCP tools
**025**: Enhanced executive summary with per-source highlights, synthesis narrative, key takeaways
**026-032**: Modern UI design system (glassmorphism, animations, accessibility, Chart.js theming)
**031**: Chart visualization system - 7 Chart.js components (radar, donut, timeline, gauge, bar, heatmap) with ChartsManager
**032**: Accessibility (WCAG 2.1 AA) and performance (Web Vitals, lazy loading, caching)

---

## Development Notes

**Git Workflow (REQUIRED):**
1. NEVER push directly to `main` branch
2. Create a feature branch for all changes: `git checkout -b feature/prd-XXX-description`
3. Make commits to the feature branch
4. Push feature branch: `git push -u origin feature/prd-XXX-description`
5. Create a Pull Request on GitHub
6. Wait for GitHub Actions tests to pass (pytest runs automatically)
7. Only merge to main after all checks pass
8. Railway auto-deploys from main when tests pass

**Adding new features:**
1. Create PRD in `/docs/` (e.g., `PRD-026_FeatureName.md`)
2. Create feature branch: `git checkout -b feature/prd-026-feature-name`
3. Implement in appropriate directory
4. Run tests locally: `pytest tests/ -v`
5. Push and create PR
6. Wait for CI to pass, then merge
7. Update this file with new commands/endpoints
8. Move PRD to `/docs/archived/` when complete

**Running Tests:**
```bash
# Run all Python tests
pytest tests/ -v

# Run frontend tests (Playwright)
npm run test:chromium
```

**Local scripts** in `/dev/scripts/` - archived scripts in `/dev/scripts/archived/`

---

**Last Updated**: 2025-12-09
