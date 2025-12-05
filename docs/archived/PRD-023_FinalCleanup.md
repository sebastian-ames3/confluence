# PRD-023: Final Cleanup & Project Wrap-Up

**Status**: Ready for Implementation
**Priority**: High
**Estimated Effort**: 1-2 hours

---

## Objective

Clean up the Confluence Hub codebase for long-term maintainability:
1. Remove development artifacts and temporary files
2. Consolidate documentation
3. Optimize CLAUDE.md for future sessions
4. Organize code structure for easy future development
5. Ensure only production-ready files remain in the repository

---

## Phase 1: Delete Artifacts (~350MB recovery)

### 1.1 Corrupted/Noise Files (DELETE)
```
C:Users14102DocumentsSebastian    # Corrupted path file from bash bug
nul                                # Windows cmd artifact
scheduler.log                      # Stale log in root (120KB)
```

### 1.2 Development Data Directories (DELETE ENTIRELY)
```
/dev/downloads/     # 181MB - test collection data
/dev/temp/          # 11MB - temporary work files
/dev/logs/          # 20KB - old dev logs
/dev/test_output/   # Empty directory
```

### 1.3 Dashboard Screenshots (DELETE)
```
/downloads/dashboard_clean.png      # 1.8MB
/downloads/dashboard_final.png      # 1.9MB
/downloads/dashboard_screenshot.png # 1.6MB
```

### 1.4 Python Cache (Auto-regenerated, safe to delete)
All `__pycache__/` directories and `.pyc` files will be excluded by .gitignore.

---

## Phase 2: Resolve Duplications

### 2.1 MCP Server Duplication
**Current State**:
- `/mcp/` - Newer (Dec 4), has SSE mode, actively used
- `/mcp_server/` - Older (Dec 2), stdio only

**Action**: DELETE `/mcp_server/` directory entirely. Keep `/mcp/`.

### 2.2 Test Duplication
**Current State**:
- `/tests/` - Production tests (keep)
- `/dev/tests/` - Development tests (review)

**Action**: Audit `/dev/tests/` - if duplicates of `/tests/`, delete. Keep only unique test utilities.

---

## Phase 3: Archive Development Scripts

### 3.1 Scripts to ARCHIVE (move to `/dev/scripts/archived/`)
Debug and one-time setup scripts no longer needed:
```
debug_kt_login.py
debug_macro42_selenium.py
debug_scorer.py
get_channel_ids_simple.py
get_youtube_channel_ids.py
get_discord_channel_ids.py
test_3_items.py
test_analysis_sample.py
test_cleanup.py
test_confluence_scorer.py
test_cross_reference.py
test_discord_collector.py
test_image_intelligence.py
test_kt_technical.py
test_macro42_selenium.py
test_multi_source_analysis.py
```

### 3.2 Scripts to KEEP (active use)
```
discord_local.py          # Primary Discord collector
macro42_local.py          # Primary 42 Macro collector
init_database.py          # DB setup
run_migrations.py         # Schema migrations
seed_data.py              # Initial data
run_discord_collection.bat # Windows automation
run_macro42_collection.bat # Windows automation
```

---

## Phase 4: Consolidate Documentation

### 4.1 Create Clean Documentation Structure
```
/docs/
├── CLAUDE.md              # PRIMARY context file (moved from dev/docs)
├── README.md              # Symlink to root or keep separate
├── DEPLOYMENT.md          # How to deploy
├── ARCHITECTURE.md        # System design (consolidate from PRD-MASTER)
└── archived/
    ├── PRD-001.md through PRD-022.md  # Completed PRDs
    └── future-ideas/
        ├── PRD_AutomatedCleanup.md
        ├── PRD_ChartIntelligence.md
        ├── PRD_DashboardEnhancements.md
        └── PRD_TranscriptChartMatching.md
```

### 4.2 Files to DELETE (stale/duplicate)
```
/dev/TOMORROW_PLAN.md      # Historical planning, outdated
/dev/CHANGELOG.md          # Duplicate
/dev/README.md             # Sparse, redundant
```

---

## Phase 5: Optimize CLAUDE.md

Create new root-level `CLAUDE.md` optimized for Claude Code sessions:

```markdown
# Macro Confluence Hub

Personal investment research aggregation system. Collects from 5 sources, applies AI analysis, surfaces confluence via web dashboard and Claude Desktop MCP.

**Version**: 1.5.0 (Dec 2025) | **Status**: Production

---

## Quick Reference

### Generate New Synthesis
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

---

## Environment

**Production**: Railway
**Auth**: HTTP Basic (`sames3` / `Spotswood1`)
**Database**: SQLite on Railway volume
**AI**: Claude Sonnet 4, Whisper API

---

## Completed PRDs

| PRD | Feature |
|-----|---------|
| 001-011 | Foundation, agents, dashboard |
| 012-013 | Dashboard simplification, MCP |
| 014-017 | Deployment, security, polish |
| 018-019 | Video transcription, deduplication |
| 020-021 | Actionable synthesis v2, Research hub v3 |
| 022 | MCP SSE mode for Claude Desktop |
| 023 | Final cleanup (this PRD) |

---

**Last Updated**: 2025-12-05
```

---

## Phase 6: Update .gitignore

Add explicit rules:
```gitignore
# Development artifacts
/downloads/*.png
/dev/downloads/
/dev/temp/
/dev/logs/
/dev/test_output/

# Old MCP server (removed)
/mcp_server/

# Scheduler logs
scheduler.log
```

---

## Phase 7: Final Git Cleanup

### Commands to Execute
```bash
# 1. Delete corrupted files
rm -f "C:Users14102DocumentsSebastian"
rm -f nul
rm -f scheduler.log

# 2. Delete dev artifacts
rm -rf dev/downloads/
rm -rf dev/temp/
rm -rf dev/logs/
rm -rf dev/test_output/

# 3. Delete old MCP server
rm -rf mcp_server/

# 4. Delete dashboard screenshots
rm -f downloads/*.png

# 5. Create archive directories
mkdir -p dev/scripts/archived
mkdir -p docs/archived
mkdir -p docs/archived/future-ideas

# 6. Move archived scripts
mv dev/scripts/debug_*.py dev/scripts/archived/
mv dev/scripts/get_*.py dev/scripts/archived/
mv dev/scripts/test_*.py dev/scripts/archived/

# 7. Move archived docs
mv dev/docs/PRD-0*.md docs/archived/
mv dev/docs/PRD_*.md docs/archived/future-ideas/

# 8. Move CLAUDE.md to root
cp dev/docs/CLAUDE.md ./CLAUDE.md  # Will be replaced with optimized version

# 9. Delete stale docs
rm -f dev/TOMORROW_PLAN.md
rm -f dev/CHANGELOG.md
rm -f dev/README.md

# 10. Commit cleanup
git add -A
git commit -m "[PRD-023] Final cleanup and project organization

- Remove development artifacts (~350MB)
- Delete old mcp_server/ (replaced by /mcp/)
- Archive completed PRDs and debug scripts
- Move CLAUDE.md to root with optimized content
- Update .gitignore for cleaner repo
- Organize documentation structure

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 11. Push to Railway
git push origin main
```

---

## Post-Cleanup Structure

```
confluence/
├── CLAUDE.md                 # PRIMARY context for Claude sessions
├── README.md                 # Project overview
├── .env                      # Credentials (gitignored)
├── .env.example              # Template
├── .gitignore                # Updated exclusions
├── requirements.txt          # Dependencies
├── railway.json              # Deployment config
│
├── agents/                   # AI agents (10 files)
├── backend/                  # FastAPI app
│   ├── routes/              # API endpoints
│   ├── utils/               # Helpers
│   ├── app.py               # Main app
│   └── models.py            # SQLAlchemy models
├── collectors/               # Collection logic
├── config/                   # Configuration
├── database/                 # SQLite + migrations
├── frontend/                 # Dashboard UI
├── mcp/                      # Claude Desktop MCP
├── tests/                    # Unit tests
│
├── dev/                      # Development files
│   ├── scripts/             # Active collection scripts
│   │   ├── discord_local.py
│   │   ├── macro42_local.py
│   │   ├── *.bat            # Windows automation
│   │   └── archived/        # Old scripts
│   └── docs/                # Development docs
│
├── docs/                     # Documentation
│   ├── archived/            # Completed PRDs
│   │   ├── PRD-001.md ... PRD-023.md
│   │   └── future-ideas/    # Proposed features
│   ├── DEPLOYMENT.md
│   └── ARCHITECTURE.md
│
├── downloads/                # Collection temp (empty)
├── temp/                     # Temp files (empty)
└── logs/                     # Production logs
```

---

## Success Criteria

- [ ] Repository size reduced by ~300MB+
- [ ] No corrupted or artifact files
- [ ] Single MCP implementation (`/mcp/`)
- [ ] CLAUDE.md at root with optimized content
- [ ] Clear separation: production vs archived
- [ ] Easy to find key files for future development
- [ ] Clean git history with meaningful commit

---

## Future Development Notes

When adding new features:
1. Create PRD in `/docs/` (e.g., `PRD-024_FeatureName.md`)
2. Implement in appropriate directory
3. Update CLAUDE.md with new commands/endpoints
4. Move PRD to `/docs/archived/` when complete
5. Keep `/dev/scripts/` for local-only utilities

---

**Created**: 2025-12-05
**Author**: Claude Code
