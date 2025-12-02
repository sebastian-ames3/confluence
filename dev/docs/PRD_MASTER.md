# PRD MASTER - Macro Confluence Hub

**Version**: 1.0  
**Date**: 2025-11-18  
**Owner**: Sebastian Ames  
**Status**: Planning

---

## Executive Summary

A personal investment research aggregation platform that automatically collects macro analysis from 6+ premium sources, uses AI sub-agents to extract insights, scores content against a 7-pillar investment framework, and surfaces high-conviction ideas via a clean web dashboard.

**Timeline**: 4 weeks to MVP  
**Budget**: ~$75/month operational costs (Claude API + Whisper API)  
**Success Criteria**: 95% automated collection success rate, <30 min/day manual review time

---

## Product Vision

### Problem
Sebastian pays $1000s/month for premium macro research but manually synthesizing:
- 42macro PDFs and videos
- Options Insight Discord (text, charts, videos)
- Twitter analysis from multiple accounts
- YouTube long-form content
- Substack newsletters

**Current State**: 2+ hours/day manually reviewing, tracking themes in head/notes  
**Desired State**: Automated system surfaces high-conviction confluent ideas in <30 min/day

### Solution
Intelligent research hub that:
1. Collects content automatically (6am, 6pm, on-demand)
2. AI agents analyze text, PDFs, images, video transcripts
3. Scores against institutional-grade confluence framework
4. Tracks conviction evolution over time (Bayesian)
5. Presents unified view in mobile-friendly dashboard

---

## Development Phases

### Phase 0: Project Setup
**Duration**: 1 day  
**PRD**: PRD-001

**Deliverables**:
- GitHub repo structure
- CHANGELOG.md initialized
- All PRD documents created
- GitHub Issues + Milestones configured
- Development environment setup

**Success Criteria**:
- [ ] All PRDs reviewed and approved by Sebastian
- [ ] First commit pushed to main branch
- [ ] GitHub Issues created for all Phase 1 tasks

---

### Phase 1: Foundation (Week 1)
**Duration**: 5-7 days  
**PRDs**: PRD-002, PRD-003, PRD-004

#### PRD-002: Database Schema & Infrastructure
**What**: SQLite database design for storing raw content, analyzed data, confluence scores

**Key Tables**:
- `sources` - Configuration for each data source
- `raw_content` - Everything collected (text, file paths, URLs)
- `analyzed_content` - AI agent outputs
- `confluence_scores` - Pillar scores over time
- `themes` - Active investment ideas being tracked

**Success Criteria**:
- [ ] Schema designed and reviewed
- [ ] Migration system in place
- [ ] CRUD operations tested
- [ ] Sample data inserted and queryable

#### PRD-003: Content Classifier Agent
**What**: First AI agent - triages all incoming content

**Capabilities**:
- Detect content type (text, PDF, video, image)
- Identify source
- Assign priority
- Route to appropriate specialized agents

**Success Criteria**:
- [ ] Correctly classifies 20 sample items from each source
- [ ] Unit tests passing
- [ ] Integration with database working
- [ ] Response time <2 seconds per item

#### PRD-004: Basic Collectors (No AI)
**What**: Raw data collection modules for each source

**Components**:
- 42macro web scraper (login + download PDFs/videos)
- Discord local script (discord.py-self)
- Twitter scraper (text + video links)
- YouTube API integration
- Substack RSS parser

**Success Criteria**:
- [ ] Each collector runs standalone
- [ ] Data saved to database
- [ ] Error handling for rate limits, auth failures
- [ ] 42macro: Download 5 PDFs successfully
- [ ] Discord: Collect 1 day of messages from 5 channels
- [ ] Twitter: Scrape 20 tweets from @KTTECHPRIVATE
- [ ] YouTube: Fetch metadata for 5 videos
- [ ] Substack: Parse latest 10 posts

---

### Phase 2: Intelligence Layer (Week 2)
**Duration**: 7 days  
**PRDs**: PRD-005, PRD-006, PRD-007

#### PRD-005: Transcript Harvester Agent
**What**: Video → transcription → analysis pipeline

**Capabilities**:
- Download videos (YouTube, Zoom/Webex, Twitter)
- Extract audio
- Whisper API transcription
- Claude analysis: themes, tickers, sentiment, conviction

**Success Criteria**:
- [ ] Transcribe 5 Imran Discord videos correctly
- [ ] Transcribe 3 Darius Dale 42macro videos
- [ ] Extract key themes with >90% accuracy (Sebastian validates)
- [ ] Proper handling of video download failures
- [ ] Cost per video <$0.50

#### PRD-006: PDF Analyzer Agent
**What**: PDF → structured insights

**Capabilities**:
- Text extraction (handle various PDF formats)
- Table extraction
- Claude analysis for macro themes, valuations, positioning

**Success Criteria**:
- [ ] Process 10 42macro PDFs successfully
- [ ] Extract tables from "Around the Horn" reports
- [ ] Identify KISS model signals
- [ ] Handle encrypted/scanned PDFs gracefully
- [ ] Analysis quality validated by Sebastian on 5 PDFs

#### PRD-007: Image Intelligence Agent
**What**: Charts/graphs → data extraction

**Capabilities**:
- OCR for text in images
- Claude vision for chart interpretation (volatility surfaces, technical levels, positioning charts)

**Success Criteria**:
- [ ] Interpret 10 Options Insight charts correctly
- [ ] Extract data from volatility surface charts
- [ ] Identify key technical levels from chart images
- [ ] Handle various chart styles/formats

---

### Phase 3: Confluence Engine (Week 3)
**Duration**: 7 days  
**PRDs**: PRD-008, PRD-009

#### PRD-008: Confluence Scorer Agent
**What**: Score analyzed content against 7-pillar framework

**Capabilities**:
- Apply Sebastian's scoring rubric (0-2 per pillar)
- Generate reasoning for each score
- Define falsification criteria
- Calculate total/core scores
- Determine if meets threshold (6-7/10 core + hybrid pillar)

**Success Criteria**:
- [ ] Score 30 pieces of analyzed content
- [ ] Sebastian validates scores: >90% alignment with his judgment
- [ ] Reasoning is clear and actionable
- [ ] Falsification criteria are specific and measurable
- [ ] Performance: <5 seconds per item

#### PRD-009: Cross-Reference Agent
**What**: Find confluence patterns across sources and time

**Capabilities**:
- Compare themes across sources
- Identify when 2+ sources agree (confluence)
- Flag contradictions
- Bayesian updating of conviction over time
- Track theme evolution

**Success Criteria**:
- [ ] Correctly identify 5 confluent themes from 2 weeks of data
- [ ] Show conviction evolution over time
- [ ] Flag contradictions between sources
- [ ] Bayesian update calculation verified
- [ ] Dashboard visualization shows clear trends

---

### Phase 4: Dashboard & Deployment (Week 4)
**Duration**: 7 days  
**PRDs**: PRD-010, PRD-011

#### PRD-010: Web Dashboard
**What**: React/vanilla JS frontend for viewing confluence data

**Pages**:
1. **Today's View**: Latest analysis, top confluence scores
2. **Theme Tracker**: Active investment ideas, strength over time
3. **Source Browser**: Drill into specific sources
4. **Confluence Matrix**: Heatmap of pillar scores
5. **Historical**: Theme evolution over time

**Features**:
- Mobile-responsive
- Real-time updates
- Manual triggers (run collection now, re-analyze)
- Export to CSV/JSON

**Success Criteria**:
- [ ] All 5 pages functional
- [ ] Loads <2 seconds
- [ ] Works on mobile (iPhone tested)
- [ ] Manual triggers work from UI
- [ ] Sebastian can navigate intuitively

#### PRD-011: Railway Deployment & Scheduler
**What**: Deploy to Railway with automated scheduling

**Components**:
- FastAPI backend deployed
- Frontend served
- SQLite persistent storage configured
- Cron jobs: 6am, 6pm data collection + analysis
- Environment variables configured
- Discord local script setup on Sebastian's laptop

**Success Criteria**:
- [ ] Accessible at custom Railway URL
- [ ] 6am collection runs automatically for 3 consecutive days
- [ ] 6pm collection runs automatically for 3 consecutive days
- [ ] Discord script runs on Sebastian's laptop at scheduled times
- [ ] Manual on-demand collection works
- [ ] All credentials secure (not in git)
- [ ] Monitoring/logging set up

---

## GitHub Structure

### Milestones
- **Milestone 1**: Phase 0 - Setup (1 day)
- **Milestone 2**: Phase 1 - Foundation (Week 1)
- **Milestone 3**: Phase 2 - Intelligence (Week 2)
- **Milestone 4**: Phase 3 - Confluence (Week 3)
- **Milestone 5**: Phase 4 - Deploy (Week 4)

### Issue Labels
- `agent` - AI sub-agent development
- `collector` - Data collection module
- `database` - Schema or query work
- `frontend` - Dashboard UI
- `infrastructure` - DevOps, deployment
- `testing` - Test suite work
- `bug` - Something broken
- `documentation` - Docs/PRD updates

### Branch Strategy
```
main (protected)
  └── feature/[prd-number]-[short-description]
      Examples:
      - feature/002-database-schema
      - feature/003-content-classifier
      - feature/005-transcript-harvester
```

### Commit Format
```
[PRD-XXX] Short description

Longer description of what changed and why.

Closes #[issue-number]
```

Example:
```
[PRD-003] Implement Content Classifier Agent

Added ContentClassifierAgent class with Claude API integration.
Includes routing logic for video, PDF, image, and text content.

Closes #5
```

---

## Testing Requirements

### Per PRD Requirements
- **Unit Tests**: Every agent module, every collector
- **Integration Tests**: Agent → Database, Collector → Agent pipelines
- **Manual Validation**: Sebastian reviews outputs for accuracy

### Coverage Goals
- Agents: 90%+ coverage
- Collectors: 80%+ coverage
- Database operations: 95%+ coverage

### CI/CD Pipeline
- Run tests on every PR
- Block merge if tests fail
- Deploy to Railway on merge to main

---

## Risk Management

### High-Risk Items
1. **Discord Collection Reliability**
   - Mitigation: Robust error handling, retry logic, Sebastian laptop uptime monitoring

2. **Video Transcription Cost**
   - Mitigation: Cache transcripts, limit to key videos only, monitor monthly spend

3. **Confluence Scoring Accuracy**
   - Mitigation: Sebastian validation on 30+ items before trusting, continuous refinement

4. **API Rate Limits**
   - Mitigation: Respect limits, implement backoff, queue requests

### Medium-Risk Items
1. **Railway Downtime**: Have local fallback for critical periods
2. **Auth Changes**: Monitor for login flow changes on 42macro/Twitter
3. **Data Volume Growth**: Plan for SQLite → Postgres migration path

---

## Success Metrics (Post-Launch)

### Week 1 Post-MVP
- [ ] 7 consecutive days of successful 6am + 6pm runs
- [ ] Zero data loss incidents
- [ ] Sebastian reviews dashboard daily

### Week 2-4 Post-MVP
- [ ] Sebastian validates 30 confluence scores: >85% accuracy
- [ ] Time spent reviewing reduced from 2hrs → <30min daily
- [ ] 3+ high-conviction ideas identified and acted upon

### Month 2
- [ ] Historical tracking shows clear conviction trends
- [ ] Bayesian updates proving useful for timing
- [ ] Sebastian considers expanding to include more sources

---

## Dependencies

### External APIs
- Claude API (Anthropic)
- Whisper API (OpenAI)
- YouTube Data API v3 (Google)

### Python Libraries
- `discord.py-self` - Discord collection
- `requests` - HTTP requests
- `beautifulsoup4` - Web scraping
- `pypdf2` / `pdfplumber` - PDF parsing
- `fastapi` - Backend API
- `sqlalchemy` - Database ORM
- `pytest` - Testing
- `schedule` - Cron jobs

### Infrastructure
- GitHub (version control, CI/CD)
- Railway (hosting, deployment)

---

## Communication Plan

### Daily Updates
- CHANGELOG.md updated with every significant change
- Commits reference GitHub Issues

### Weekly Review
- End of each phase: Sebastian reviews deliverables
- Adjust next phase PRD if needed based on learnings

### Blockers
- If stuck >4 hours: Document blocker in GitHub Issue, propose alternatives

---

### Phase 5: Simplification & Chat Integration
**Duration**: 3-5 days
**PRDs**: PRD-012, PRD-013

#### PRD-012: Dashboard Simplification & Synthesis Agent
**What**: Transform complex scoring dashboard into simple research synthesis assistant

**Key Changes**:
- Strip dashboard to single status page
- Create Synthesis Agent with macro analyst persona
- Let Claude naturally weight evidence (internal scoring only)
- Generate 1-3 paragraph summaries after each collection

**Success Criteria**:
- [ ] Simple dashboard showing collection status + synthesis
- [ ] Synthesis Agent generating quality summaries
- [ ] Synthesis triggered after scheduled collections
- [ ] Sebastian validates synthesis quality

#### PRD-013: MCP Server for Claude Desktop
**What**: Enable natural language queries against collected research via Claude Desktop

**Tools Exposed**:
- `search_content` - Query research by keyword
- `get_synthesis` - Retrieve latest AI summary
- `get_themes` - List tracked macro themes
- `get_recent` - Get recent collections by source
- `get_source_view` - Get source's view on topic

**Success Criteria**:
- [ ] MCP server connects to Claude Desktop
- [ ] All 5 tools functional
- [ ] Sebastian can query research conversationally
- [ ] Documentation complete

---

### Phase 6: Production Hardening
**Duration**: 3-5 days
**PRDs**: PRD-014, PRD-015, PRD-016, PRD-017

#### PRD-014: Deployment & Infrastructure Fixes
**What**: Fix critical deployment blockers identified in production readiness review

**Key Changes**:
- Add FFmpeg, Chromium to Railway nixPackages
- Auto-initialize database on first deploy
- Create API trigger endpoints for collection
- Implement GitHub Actions scheduler (Railway Hobby has no cron)

**Success Criteria**:
- [ ] Railway deployment includes system dependencies
- [ ] Database auto-initializes on empty volume
- [ ] GitHub Actions triggers collection at 6am/6pm EST
- [ ] End-to-end deployment tested

#### PRD-015: Security Hardening
**What**: Implement security best practices

**Key Changes**:
- HTTP Basic Auth on all protected endpoints
- API rate limiting (slowapi)
- Move Discord channel IDs to environment variables
- Replace pickle with JSON for cookie storage
- Remove hardcoded URLs

**Success Criteria**:
- [ ] Authentication required for dashboard/API
- [ ] Rate limiting prevents API abuse
- [ ] No secrets in version control
- [ ] Secure cookie handling

#### PRD-016: MCP Server API Proxy Refactor
**What**: Fix architecture gap where MCP server can't access Railway database

**Key Changes**:
- MCP tools call Railway API via HTTP (not local SQLite)
- API client with authentication support
- Graceful error handling for network failures
- Updated Claude Desktop configuration

**Success Criteria**:
- [ ] MCP server fetches data from Railway API
- [ ] All 5 tools work with API proxy pattern
- [ ] Claude Desktop integration functional

#### PRD-017: Polish & Reliability
**What**: Address remaining issues from production review

**Key Changes**:
- Version consistency (update to 1.0.0)
- Dependency cleanup (remove duplicates, update anthropic SDK)
- Basic agent tests with mocked Claude responses
- Database backup script
- UsageLimiter timezone fix (explicit UTC)
- Frontend button implementation
- Dashboard unification

**Success Criteria**:
- [ ] Version 1.0.0 consistent across codebase
- [ ] Agent tests passing with mocks
- [ ] Backup script functional
- [ ] All frontend buttons implemented

---

## Next Steps

1. **Phase 6 Implementation**: Begin PRD-014 (Deployment Fixes) - CRITICAL
2. **Security**: Implement PRD-015 after infrastructure fixes
3. **MCP Fix**: Implement PRD-016 to restore Claude Desktop functionality
4. **Polish**: Complete PRD-017 for final production readiness

---

## Appendix: PRD List

### Phase 0-4 (Complete)
- **PRD-001**: Project Setup & Infrastructure ✅
- **PRD-002**: Database Schema & Infrastructure ✅
- **PRD-003**: Content Classifier Agent ✅
- **PRD-004**: Basic Collectors (No AI) ✅
- **PRD-005**: Transcript Harvester Agent ✅
- **PRD-006**: PDF Analyzer Agent ✅
- **PRD-007**: Image Intelligence Agent ✅
- **PRD-008**: Confluence Scorer Agent ✅
- **PRD-009**: Cross-Reference Agent ✅
- **PRD-010**: Web Dashboard ✅
- **PRD-011**: Railway Deployment & Scheduler ✅

### Phase 5 (Complete)
- **PRD-012**: Dashboard Simplification & Synthesis Agent ✅
- **PRD-013**: MCP Server for Claude Desktop Integration ✅

### Phase 6 (Complete)
- **PRD-014**: Deployment & Infrastructure Fixes ✅
- **PRD-015**: Security Hardening ✅
- **PRD-016**: MCP Server API Proxy Refactor ✅
- **PRD-017**: Polish & Reliability ✅

---

**Total Estimated Development Time**: 35-40 days (4 weeks + Phase 5 + Phase 6)
**Estimated API Costs**: $50-75/month
**Primary Risk**: Railway deployment system dependencies
**Primary Success Factor**: Secure, reliable production deployment

---

**Document Status**: Updated for Phase 6
**Last Updated**: 2025-12-01
