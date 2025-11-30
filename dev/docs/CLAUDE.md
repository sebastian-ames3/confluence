# Macro Confluence Hub - Project Context

## Overview
Personal investment research aggregation system. Collects macro analysis from 5 premium sources, applies AI analysis via 10 agents, scores confluence across 7 investment pillars, and provides a web dashboard + Claude Desktop integration.

**Status**: v1.0.0 MVP Complete (2025-11-30) | ~15,000 lines production code

---

## Current State

| Component | Status | Details |
|-----------|--------|---------|
| Collectors | 5 active | Discord, YouTube, Substack, 42 Macro, KT Technical |
| AI Agents | 10 complete | 4,456 lines total |
| Backend | Complete | FastAPI, 6 route modules, WebSocket |
| Frontend | Complete | 6 pages, mobile-responsive |
| MCP Server | Complete | 5 tools for Claude Desktop |
| Database | Complete | SQLite with Bayesian tracking |

---

## Data Sources

| Source | Method | Content |
|--------|--------|---------|
| Discord (Options Insight) | discord.py-self (local) | Text, charts, PDFs, Zoom links |
| YouTube | API v3 | 4 channels (42 Macro, Forward Guidance, etc.) |
| Substack | RSS | Visser Labs articles |
| 42 Macro | Selenium | PDFs (Around The Horn, Macro Scouting Report) |
| KT Technical | Session auth | Weekly blog posts + chart images |

**Schedule**: 6am/6pm automated (Discord runs locally via Task Scheduler)

---

## AI Agents

| Agent | Lines | Purpose |
|-------|-------|---------|
| Content Classifier | 334 | Routes content to appropriate agents |
| Transcript Harvester | 363 | Video → Whisper → Claude analysis |
| PDF Analyzer | 810 | Text/image extraction + analysis |
| Image Intelligence | 450 | Claude Vision for charts |
| Visual Content Classifier | 380 | Lightweight image routing |
| Confluence Scorer | 490 | 7-pillar framework scoring |
| Cross-Reference | 637 | Bayesian conviction, theme clustering |
| Transcript Chart Matcher | 336 | Cost optimization for 42 Macro |
| Cleanup Manager | 473 | Storage management |
| Synthesis Agent | 320 | Research summaries |

---

## MCP Server (Claude Desktop)

5 tools for natural language queries:
- `search_content` - Search by keyword
- `get_synthesis` - AI-generated summaries
- `get_themes` - Tracked investment themes
- `get_recent` - Recent content by source
- `get_source_view` - Source's view on topic

**Setup**: Add to `%APPDATA%\Claude\claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "confluence-hub": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "C:/path/to/confluence",
      "env": {"DATABASE_PATH": "C:/path/to/confluence/database/confluence.db"}
    }
  }
}
```

---

## 7-Pillar Confluence Framework

**Core (0-2 each, max 10)**:
1. Macro data & regime
2. Fundamentals
3. Valuation & capital cycle
4. Positioning/flows
5. Policy/narrative

**Hybrid (0-2 each)**:
6. Price action/technicals
7. Options/volatility

**Threshold**: Core ≥6-7 AND at least one hybrid = 2/2

---

## Tech Stack

- **Backend**: Python/FastAPI
- **Database**: SQLite
- **Frontend**: Vanilla JS, Chart.js
- **AI**: Claude API (Sonnet), Whisper API
- **Deployment**: Railway
- **MCP**: Official Anthropic SDK (Python 3.10+)

---

## Key Files

```
confluence/
├── agents/          # 10 AI agents
├── collectors/      # 5 data collectors
├── backend/         # FastAPI app, routes
├── frontend/        # 6 HTML pages + CSS/JS
├── mcp_server/      # Claude Desktop integration
├── database/        # SQLite + migrations
└── dev/docs/        # PRDs, CHANGELOG
```

---

## Development Rules

1. **Never push directly to main** - Always use feature branches + PRs
2. **Branch naming**: `feature/`, `fix/`, `update/`
3. **Commits**: Reference PRD/issue numbers
4. **Tests**: Must pass before merge

---

## API Costs

- Claude: ~$40/month
- Whisper: ~$20/month
- **Total**: ~$60/month

---

## User Context

**Sebastian Ames**: Semi-discretionary macro/options trader. Coding beginner. Prefers simple, transparent code over frameworks. Values quick iteration and frequent commits.

---

**Last Updated**: 2025-11-30
