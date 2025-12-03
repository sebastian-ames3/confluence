# Macro Confluence Hub - Project Context

## Overview
Personal investment research aggregation system. Collects macro analysis from 5 sources, applies AI analysis, and provides web dashboard + Claude Desktop integration.

**Status**: v1.3.0 (2025-12-03) | Full pipeline operational with duplicate detection

---

## Current State (Dec 3, 2025)

| Component | Status |
|-----------|--------|
| Discord Collection | Working - uploads to Railway via `--railway-api` |
| 42 Macro Collection | Working - PDFs and videos via `macro42_local.py` |
| Content Analysis | Working - `/api/analyze/classify-batch` |
| Synthesis Generation | Working - `/api/synthesis/generate` |
| Web Dashboard | Deployed at Railway |
| MCP Server | Ready for Claude Desktop |
| Duplicate Detection | Enabled - all collectors check before saving |

**Next Session**: Set up Windows Task Scheduler for 42 Macro collection (after Discord).

---

## PRD Status

| PRD | Name | Status |
|-----|------|--------|
| 001-011 | Foundation, Agents, Dashboard | Complete |
| 012 | Dashboard Simplification | Complete |
| 013 | MCP Server | Complete |
| 014 | Deployment & Infrastructure | Complete |
| 015 | Security Hardening | Complete |
| 016 | MCP API Proxy Refactor | Complete |
| 017 | Polish & Reliability | Complete |
| 018 | Video Transcription | Not started |
| 019 | Duplicate Detection | Complete |

---

## Key Commands

**Discord Collection (run locally)**:
```bash
cd "C:\Users\14102\Documents\Sebastian Ames\Projects\Confluence"
python dev/scripts/discord_local.py --railway-api
```

**42 Macro Collection (run locally)**:
```bash
cd "C:\Users\14102\Documents\Sebastian Ames\Projects\Confluence"
python dev/scripts/macro42_local.py --railway-api
```

**Trigger Analysis**:
```bash
curl -X POST -u sames3:Spotswood1 https://confluence-production-a32e.up.railway.app/api/analyze/classify-batch
```

**Generate Synthesis**:
```bash
curl -X POST -u sames3:Spotswood1 -H "Content-Type: application/json" -d '{"time_window": "7d"}' https://confluence-production-a32e.up.railway.app/api/synthesis/generate
```

---

## Data Flow

1. **Collect**: `discord_local.py --railway-api` → uploads to Railway
2. **Analyze**: `/api/analyze/classify-batch` → classifies content
3. **Synthesize**: `/api/synthesis/generate` → AI research summary

---

## Data Sources

| Source | Method | Status |
|--------|--------|--------|
| Discord (Options Insight) | discord.py-self (local) | Active |
| YouTube | API v3 | Configured |
| Substack | RSS | Configured |
| 42 Macro | Selenium | Configured |
| KT Technical | Session auth | Configured |

---

## Tech Stack

- **Backend**: Python/FastAPI, SQLite
- **Frontend**: Vanilla JS, Chart.js
- **AI**: Claude Sonnet 4, Whisper API
- **Deployment**: Railway
- **Auth**: HTTP Basic (sames3/Spotswood1)

---

## Key Files

```
confluence/
├── dev/scripts/discord_local.py  # Discord collector (run locally)
├── dev/scripts/macro42_local.py  # 42 Macro collector (run locally)
├── backend/routes/synthesis.py   # Synthesis API
├── backend/routes/analyze.py     # Analysis API
├── backend/routes/collect.py     # Collection API (with duplicate detection)
├── backend/utils/deduplication.py # Duplicate detection utility
├── agents/synthesis_agent.py     # AI synthesis
└── mcp_server/                   # Claude Desktop integration
```

---

## Environment Variables (Railway)

```
CLAUDE_API_KEY=sk-ant-...
AUTH_USERNAME=sames3
AUTH_PASSWORD=Spotswood1
DISCORD_CHANNEL_IDS=...
```

---

**Last Updated**: 2025-12-03
