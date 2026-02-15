# Macro Confluence Hub

Personal investment research aggregation system. Collects from 5 sources, applies AI analysis, surfaces confluence via web dashboard and Claude Desktop MCP.

**Status**: Production

---

## Quick Reference

### Generate Synthesis
```bash
curl -X POST -u $AUTH_USERNAME:$AUTH_PASSWORD -H "Content-Type: application/json" \
  -d '{"time_window": "7d"}' \
  $RAILWAY_API_URL/api/synthesis/generate
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
curl -X POST -u $AUTH_USERNAME:$AUTH_PASSWORD \
  $RAILWAY_API_URL/api/analyze/classify-batch
```

---

## Architecture

```
Collectors (Local) ──> Backend (Railway) ──> Dashboard (Railway)
                              │
                              v
                       MCP Server (Claude Desktop)
```

### Data Flow
1. **Collect**: Local scripts upload to Railway API
2. **Analyze**: `/api/analyze/classify-batch` runs AI analysis (includes compass image extraction for Discord)
3. **Synthesize**: `/api/synthesis/generate` runs per-source analysis + merge architecture
4. **View**: Dashboard or Claude Desktop MCP tools

### Synthesis Pipeline
Each source is analyzed independently with full content (no truncation), then results are merged for cross-source confluence detection. Quality evaluation and theme extraction run after every synthesis.

Source weights: 42macro=1.5, discord=1.5, kt_technical=1.2, substack=1.0, youtube=0.8

---

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `/agents/` | AI agents (synthesis, scoring, analysis, theme extraction) |
| `/backend/` | FastAPI app, routes, models |
| `/collectors/` | Source-specific collection logic |
| `/frontend/` | Dashboard (vanilla JS + Chart.js) |
| `/mcp/` | Claude Desktop MCP server |
| `/dev/scripts/` | Local collection scripts |
| `/tests/` | Unit tests (641 tests) |
| `/docs/archived/` | Completed PRDs |

---

## Data Sources

| Source | Type | Collection |
|--------|------|------------|
| Discord (Options Insight) | Real-time trades | discord.py-self (local) |
| 42 Macro | Institutional research | Selenium (local) |
| KT Technical | Elliott Wave analysis | Session auth |
| YouTube | Macro commentary (4 channels: Moonshots, Forward Guidance, Jordi Visser, 42 Macro) | API v3 |
| Substack | Thematic research | RSS |

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/synthesis/generate` | POST | Generate synthesis (schema 5.0) |
| `/api/synthesis/latest` | GET | Get most recent synthesis |
| `/api/analyze/classify-batch` | POST | Run analysis on unprocessed content |
| `/api/collect/discord` | POST | Upload Discord content |
| `/api/dashboard/today` | GET | Dashboard summary data |
| `/api/symbols` | GET | List tracked symbols with state |
| `/api/symbols/{symbol}` | GET | Full symbol detail with levels |
| `/api/symbols/confluence/opportunities` | GET | High-confluence symbol setups |
| `/api/health/sources` | GET | All source health status |
| `/api/health/sources/{source}` | GET | Detailed health for specific source |
| `/api/health/transcription` | GET | Transcription queue status |
| `/api/health/alerts` | GET | Active system alerts |
| `/api/health/check-alerts` | POST | Trigger alert check |
| `/api/heartbeat/{source}` | POST | Record source heartbeat |
| `/api/quality/latest` | GET | Quality score for latest synthesis |
| `/api/quality/history` | GET | Quality score history with filters |
| `/api/quality/flagged` | GET | Syntheses with quality flags |
| `/api/quality/trends` | GET | Quality score trends over time |
| `/api/quality/{synthesis_id}` | GET | Quality score for specific synthesis |

---

## MCP Tools (Claude Desktop)

| Tool | Purpose |
|------|---------|
| `get_latest_synthesis` | Full synthesis |
| `get_executive_summary` | Quick overview |
| `get_confluence_zones` | Where sources align |
| `get_conflicts` | Where sources disagree |
| `get_attention_priorities` | Ranked focus areas |
| `get_source_stance` | Source breakdown detail |
| `get_catalyst_calendar` | Upcoming events |
| `get_re_review_recommendations` | Older research now relevant |
| `search_research` | Search content |
| `list_recent_content` | Browse recent videos, PDFs, articles |
| `get_content_detail` | Full content/transcript for a specific item |
| `get_themes` | All tracked themes (with status filter) |
| `get_active_themes` | Currently active themes |
| `get_theme_detail` | Deep-dive into specific theme |
| `get_themes_summary` | Theme tracking stats |
| `get_symbol_analysis` | Full symbol analysis (KT + Discord) |
| `get_symbol_levels` | Price levels for symbol |
| `get_confluence_opportunities` | Aligned high-conviction setups |
| `get_trade_setup` | Trade idea for symbol |
| `get_synthesis_quality` | Quality score with grades and flags |
| `get_synthesis_history` | Browse past synthesis runs |
| `get_synthesis_by_id` | Fetch a specific past synthesis |
| `get_quality_trends` | Quality score trends over time |
| `get_quality_flagged` | Syntheses with quality issues |
| `get_system_health` | All source health status |
| `get_active_alerts` | Active system alerts |
| `get_theme_evolution` | Historical evolution data for a theme |

---

## Environment

- **Production**: Railway (https://confluence-production-a32e.up.railway.app)
- **Auth**: HTTP Basic (credentials in env vars `AUTH_USERNAME` / `AUTH_PASSWORD`)
- **Database**: SQLite on Railway volume
- **AI**: Claude Opus 4.5 (synthesis), Claude Sonnet 4 (other agents), AssemblyAI (transcription, Whisper fallback)

### Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `CLAUDE_API_KEY` | Yes | Claude API authentication |
| `AUTH_USERNAME` | Yes | HTTP Basic Auth username |
| `AUTH_PASSWORD` | Yes | HTTP Basic Auth password |
| `JWT_SECRET` | No | JWT signing key (defaults to AUTH_PASSWORD) |
| `ASSEMBLYAI_API_KEY` | No | AssemblyAI transcription (falls back to Whisper) |
| `SENTRY_DSN` | No | Sentry error monitoring |
| `RAILWAY_ENV` | No | Environment tag (development/production) |
| `SYNTHESIS_TIMEOUT` | No | Synthesis timeout in seconds (default: 600) |
| `SYNC_TRANSCRIPTION` | No | If "true", run transcription inline (default: false) |
| `ENABLE_QUALITY_EVALUATION` | No | If "true", run quality eval after synthesis (default: true) |

---

## Development

**Git Workflow (REQUIRED):**
1. NEVER push directly to `main` branch
2. Create a feature branch: `git checkout -b feature/description`
3. Commit, push, create PR on GitHub
4. Wait for GitHub Actions tests to pass (pytest runs automatically)
5. Merge to main after checks pass
6. Railway auto-deploys from main

**Running Tests:**
```bash
pytest tests/ -v
```

**Local scripts** in `/dev/scripts/` -- archived scripts in `/dev/scripts/archived/`

---

## PRDs

All PRDs (001-049) are complete. Key implementation files:

| Area | Key Files |
|------|-----------|
| Synthesis | `agents/synthesis_agent.py` (per-source + merge), `agents/synthesis_evaluator.py` (quality scoring) |
| Transcription | `agents/transcript_harvester.py` (AssemblyAI + Whisper + yt-dlp) |
| Scoring | `agents/confluence_scorer.py` (7-pillar framework) |
| Themes | `agents/theme_extractor.py` (extraction + lifecycle tracking) |
| Symbols | `agents/symbol_level_extractor.py` (compass image extraction), `backend/routes/symbols.py` |
| Collection | `collectors/` (discord, 42macro selenium, youtube API, substack RSS, kt_technical) |
| Health | `backend/routes/health.py`, `backend/services/alerting.py` |
| Security | `backend/utils/sanitization.py`, `backend/utils/rate_limiter.py`, `backend/routes/auth.py` (JWT) |
| MCP | `mcp/server.py` (27 tools, SSE + stdio) |
| Frontend | `frontend/css/main.css` (design system), `frontend/js/` (auth, symbols, quality, health managers) |

Superseded PRDs: 020 (Synthesis V2), 021 (Synthesis V3), 041 (Tiered Synthesis) -- all replaced by unified pipeline with schema 5.0.
