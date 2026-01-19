# Confluence Research Hub - Comprehensive Product Review Prompt

You are Claude Code with access to this GitHub repository. Your task is to perform a **comprehensive technical and product review** of "Confluence Research Hub" — a personal investment research aggregation tool.

---

## HARD CONSTRAINTS (NON-NEGOTIABLE)

1. **REVIEW ONLY.** Do not modify source code, configuration, infrastructure, or documentation in the repo.
2. Do not refactor, implement fixes, open PRs, or commit changes.
3. You may read files, run tests/lints in read-only manner, and generate **NEW OUTPUT FILE(S)** containing the review report only.
4. Do not provide step-by-step implementation instructions; findings and recommendations only.
5. **Use sub-agents extensively** for parallel deep-dives into each review domain.

---

## PRODUCT CONTEXT (FROZEN)

**Product Name:** Confluence Research Hub

**Purpose:**
Aggregate investment research from 5 premium macro sources (42 Macro, Discord Options Insight, YouTube channels, Substack, KT Technical), analyze content using Claude AI, and generate daily synthesis that highlights high-conviction themes where multiple independent sources align.

**Primary Persona:**
Sebastian — a sophisticated retail investor focused on macro investing who values understanding macroeconomics over generating specific trades. Wants to save time versus manual research aggregation while never missing critical insights from trusted sources.

**Core Promise:**
A daily research synthesis that accurately reflects what sources are saying, highlights important themes/ideas, and enables deeper exploration via MCP integration with Claude Desktop.

**v1 Non-Goals:**
- Direct trade generation or execution
- Multi-user support (single user only)
- Perfect precision (wrong ideas forgivable; missing info is not)
- Cost optimization (quality over cost for now)

**Current State:**
- ~15,000 lines of production code
- Deployed on Railway with GitHub Actions scheduler
- Only homepage actively used; other dashboard pages may be incomplete
- YouTube transcription was silently broken for ~1 month (86 video backlog discovered)
- MCP integration working well

**Success Metrics:**
1. User checks synthesis daily and it accurately reflects source content
2. Critical information from sources is never missed (recall > precision)
3. Time saved versus manual research aggregation

**Dominant Risk:**
Collection reliability — user went a month without realizing YouTube videos weren't being processed.

---

## WHAT YOU MUST PRODUCE (DELIVERABLES)

### Primary Output
Create: `confluence_hub_review.md`
(Clean headings, short paragraphs, bullet lists where appropriate; no giant code dumps)

### Optional (if pandoc available)
Also generate: `confluence_hub_review.docx`
If pandoc is not available, do NOT install anything; just produce the .md file.

---

## REVIEW DOMAINS (COVER ALL — USE SUB-AGENTS)

Deploy sub-agents to review each domain in parallel. Each sub-agent should produce findings that roll up into the main report.

### 1. Collection Pipeline Reliability (CRITICAL)

**Context:** YouTube transcription was broken for a month without detection. This is the highest-priority review area.

- Collector health monitoring and alerting
- Failure detection and recovery mechanisms
- Content deduplication logic (PRD-019)
- Source-specific collector implementations:
  - `youtube_collector.py` — transcription pipeline, API quota handling
  - `discord_collector.py` — local script coordination
  - `macro42_collector.py` — PDF/web scraping reliability
  - `substack_collector.py` — RSS parsing
  - `kt_technical_collector.py` — blog scraping
- Dry-run testing capability (PRD-034)
- GitHub Actions scheduler reliability
- Database write failures / silent failures
- "Last successful collection" tracking per source

**Key Question:** How would the user know if collection is failing?

### 2. AI Analysis Layer

- **Synthesis Agent** (`agents/synthesis_agent.py`)
  - Quality of output vs. user's "surface level" complaint
  - V1/V2/V3/V4 synthesis versions — which is production?
  - Token management for large content windows
  - Source attribution accuracy (PRD-040: YouTube channel names)
- **Theme Extractor** (`agents/theme_extractor.py`)
  - Theme matching/deduplication logic
  - Theme lifecycle (emerging → active → evolved → dormant)
- **PDF Analyzer** (`agents/pdf_analyzer.py`)
  - 42 Macro report parsing quality
- **Content Classifier** (`agents/content_classifier.py`)
  - Routing accuracy
- **Symbol Level Extractor** (`agents/symbol_level_extractor.py`)
  - PRD-039 implementation status

**Key Question:** Is the synthesis capturing enough depth per source, or losing fidelity in summarization?

### 3. Dead Code & Unused Features Audit

**Context:** User only uses homepage; doesn't know what else is/isn't fully built.

- Identify incomplete/abandoned features across:
  - Dashboard tabs (Sources, History, Themes, Symbols, etc.)
  - API endpoints that exist but aren't wired to UI
  - Database tables/models never populated
  - Frontend JS modules loaded but unused
  - PRDs marked "Complete" but features not functional
- CSS/JS bloat from unused components
- Orphaned database migrations
- Test files for non-existent features

**Key Question:** What can be safely removed to reduce complexity?

### 4. Database & Data Integrity

- Schema design review (`backend/models.py`, `database/schema.sql`)
- Foreign key integrity and cascade behavior
- Index effectiveness for common queries
- Data retention and cleanup policies
- Migration status (SQLite → PostgreSQL readiness per PRD-035)
- Synthesis storage (JSON blob vs. normalized)
- Theme tracking data model (PRD-024)

**Key Question:** Is the data model sound for the current use case?

### 5. API & Backend Architecture

- Route organization (`backend/routes/`)
- Authentication implementation (PRD-036: JWT + Basic Auth)
- Rate limiting configuration
- Error handling consistency
- Async vs sync patterns (PRD-035 migration status)
- Input sanitization (PRD-037)
- API documentation accuracy

**Key Question:** Are there routes that could fail silently or return misleading success?

### 6. Frontend & UX

- Homepage synthesis display
  - Is current layout supporting "depth per source" need?
  - Tier 1/2/3 expandable structure (PRD-041)
- Unused dashboard tabs — what's broken vs. incomplete?
- Mobile responsiveness
- Loading states and error handling
- Glassmorphic design consistency
- JavaScript module organization
- Accessibility (PRD-026 compliance)

**Key Question:** What UI changes would surface more source-level detail?

### 7. MCP Integration

- Tool completeness (`mcp/server.py`)
- Data freshness in MCP responses
- Error handling when synthesis unavailable
- Documentation accuracy (`mcp/README.md`)

**Key Question:** Does MCP reliably surface all collected research?

### 8. Operational Readiness

- Logging coverage and usefulness
- Health check endpoint (`/health`)
- Environment variable documentation
- Railway deployment configuration
- Secrets management
- Backup/recovery capability
- Monitoring/alerting gaps

**Key Question:** How does the user know the system is healthy?

### 9. Testing & Quality

- Test coverage analysis
- Tests for non-existent features (dead tests)
- Integration test gaps
- Playwright UI test status
- CI/CD pipeline (`pytest` in GitHub Actions)

**Key Question:** Would tests catch the YouTube transcription failure?

### 10. Security Review

- Authentication bypass risks
- SQL injection (despite ORM)
- Prompt injection protection (PRD-037)
- Sensitive data in logs
- API key exposure risks
- Cookie/session handling

**Key Question:** Any security issues for a single-user personal tool?

### 11. Code Quality & Maintainability

- Code organization and module boundaries
- Naming consistency
- Documentation accuracy (CLAUDE.md, PRDs)
- Configuration management
- Dependency management (`requirements.txt`)
- Python version compatibility

**Key Question:** Could a future maintainer understand this codebase?

---

## OUTPUT FORMAT (REPORT STRUCTURE)

Your report MUST include, in this exact order:

### 1. Executive Summary (max ~1 page)
- What it is
- Current state assessment
- Overall verdict: **Healthy / Needs Work / Critical Issues**
- Top 3 risks (ranked)

### 2. Collection Reliability Deep-Dive
Given this is the dominant risk area, provide extended analysis:
- Current failure detection mechanisms
- The YouTube gap: how it happened, how to prevent recurrence
- Source-by-source reliability assessment
- Recommended monitoring approach

### 3. Synthesis Quality Analysis
- Current output quality assessment
- Gap between V1/V2/V3/V4 implementations
- Recommendations for surfacing more source-level depth
- Token efficiency analysis

### 4. Dead Code Inventory
Comprehensive list of:
- Unused/incomplete features (with file paths)
- Safe-to-remove code
- "Complete" PRDs with non-functional features
- Estimated cleanup effort

### 5. Launch Readiness Scorecard (0–3 scale per section)

| Domain | Score | Notes |
|--------|-------|-------|
| Collection Reliability | 0-3 | |
| AI Analysis Quality | 0-3 | |
| Data Integrity | 0-3 | |
| API Stability | 0-3 | |
| Frontend Completeness | 0-3 | |
| MCP Integration | 0-3 | |
| Operational Readiness | 0-3 | |
| Security | 0-3 | |
| Code Quality | 0-3 | |

**Scoring:**
- 0 = Critical issues / non-functional
- 1 = Major issues / partially functional
- 2 = Minor issues / mostly functional
- 3 = Production ready / fully functional

### 6. Findings by Domain (Sections 1-11 above)

For each domain:
- **Summary** (2-3 sentences)
- **Critical Issues** (if any)
- **High-Priority Issues**
- **Medium/Low Issues**
- **Evidence Pointers** (file paths, function names — do NOT paste large code blocks)

### 7. Consolidated Action Items

Prioritized list with:
- Issue description
- Severity (Critical / High / Medium / Low)
- Location in codebase
- Definition of "done"
- Estimated complexity (Low / Medium / High)

### 8. Quick Wins
Issues that could be fixed in <1 hour each with high impact.

### 9. Architectural Recommendations
Higher-level suggestions for improving the system design.

### 10. Final Assessment

- **Overall Health:** Healthy / Needs Work / Critical Issues
- **Recommended Next Steps** (prioritized list of 3-5 items)
- **What's Working Well** (acknowledge strengths)

---

## PROCESS INSTRUCTIONS (HOW TO WORK)

### Phase 1: Reconnaissance
1. Scan repo structure to understand layout
2. Read `README.md`, `docs/CLAUDE.md`, `docs/PRD_MASTER.md`
3. Identify all PRDs and their status (complete vs. in-progress)
4. Map the data flow: collection → analysis → synthesis → display

### Phase 2: Sub-Agent Deployment
Deploy sub-agents for parallel review:
- **Sub-Agent A:** Collection Pipeline (all collectors, trigger routes, GitHub Actions)
- **Sub-Agent B:** AI Layer (all agents, synthesis versions)
- **Sub-Agent C:** Dead Code Audit (frontend JS, CSS, unused routes, orphan tests)
- **Sub-Agent D:** Database & API (models, routes, auth)
- **Sub-Agent E:** Frontend & MCP (UI components, MCP tools)
- **Sub-Agent F:** Ops & Security (logging, deployment, security)

### Phase 3: Cross-Reference
- Correlate findings across sub-agents
- Identify systemic issues
- Verify PRD completion claims against actual implementation

### Phase 4: Report Generation
- Synthesize sub-agent findings
- Write executive summary last (after all findings known)
- Verify all file path references are accurate

---

## CONTEXT FILES TO PRIORITIZE

**Core Architecture:**
- `backend/app.py` — FastAPI application setup
- `backend/models.py` — Database models
- `backend/routes/` — All API endpoints

**Collection Layer:**
- `collectors/` — All collector implementations
- `backend/routes/trigger.py` — Collection trigger endpoints
- `.github/workflows/scheduled-collection.yml` — Scheduler

**AI Layer:**
- `agents/` — All AI agents
- `agents/synthesis_agent.py` — Core synthesis logic

**Frontend:**
- `frontend/index.html` — Main dashboard
- `frontend/js/` — JavaScript modules
- `frontend/css/` — Stylesheets

**MCP:**
- `mcp/server.py` — MCP tool implementations
- `mcp/confluence_client.py` — API client

**Documentation:**
- `docs/CLAUDE.md` — Project context
- `docs/PRD_MASTER.md` — Roadmap
- `docs/*.md` and `docs/archived/*.md` — All PRDs

---

## BEGIN NOW

First, have each sub-agent produce a structured findings summary. Then synthesize into the final report at `confluence_hub_review.md`.

**Tone:** Direct internal review. No hype. No reassurance. Honest assessment.
