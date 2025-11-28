# Macro Confluence Hub - Project Context

## Project Overview

A personal investment research aggregation and analysis system that collects macro and market analysis from multiple paid sources, analyzes content for confluence across Sebastian's investment framework, and provides a unified dashboard for decision-making.

**Core Capability**: Bayesian confluence tracking across 7 investment pillars (macro data, fundamentals, valuation, positioning, policy, price action, options/volatility) to build conviction in investment ideas.

---

## 🎯 Current Project Status (as of 2025-11-28)

### Phase Completion
- ✅ **Phase 0**: Project Setup (Complete)
- ✅ **Phase 1**: Foundation (Complete)
  - Database schema ✅
  - Content Classifier Agent ✅
  - All 5 collectors production-ready ✅
- ✅ **Phase 2**: Intelligence Layer (Complete)
  - Transcript Harvester Agent ✅ (363 lines)
  - PDF Analyzer Agent ✅ (810 lines)
  - Image Intelligence Agent ✅ (450 lines)
- ✅ **Phase 3**: Confluence Engine (Complete)
  - Confluence Scorer Agent ✅ (490 lines)
  - Cross-Reference Agent ✅ (637 lines)
- ✅ **Phase 4**: Dashboard & Deployment (Complete)
  - Web Dashboard ✅ (All 6 pages)
  - WebSocket real-time updates ✅
  - Railway deployment configuration ✅

### What's Working Now
- **5 data collectors** collecting content from Discord, YouTube, Substack, 42 Macro, KT Technical
- **10 AI agents** fully implemented (4,456 lines total)
- **Complete web dashboard** with real-time WebSocket updates
- **Database** with full historical tracking and Bayesian updates
- **Usage limiter** for API cost control

### Implementation Summary
| Component | Files | Lines | Status |
|-----------|-------|-------|--------|
| Agents | 10 | 4,456 | ✅ Complete |
| Collectors | 5 | ~2,300 | ✅ Complete |
| Backend Routes | 6 | 1,479 | ✅ Complete |
| Database | 2 | 291 | ✅ Complete |
| Frontend | 6 pages | 639+ JS | ✅ Complete |
| Tests | 6 | 1,220 | ✅ Good coverage |

**Total codebase: ~14,000+ lines of production code**

See CHANGELOG.md for detailed completion history.

---

## User Profile

**Name**: Sebastian Ames
**Investor Type**: Semi-discretionary/hybrid macro-thematic + options trader
**Technical Level**: Coding beginner, non-software engineer
**Development Philosophy**: Vibe coding - build quickly, learn by doing, iterate
**Tech Stack Preference**: Consistent patterns, HTML/CSS/JavaScript when possible
**Development Approach**: Comprehensive Claude.md files, clear PRDs, frequent commits

---

## Business Context

### Problem Statement
Sebastian subscribes to multiple premium research services ($1000s/month) but struggles to:
- Systematically track confluence across sources
- Identify when multiple independent analyses align
- Track how views evolve over time (Bayesian updating)
- Quickly synthesize information for trading decisions

### Success Criteria
1. Automated data collection from all sources (6am, 6pm, on-demand)
2. AI-powered content analysis extracting key themes, sentiment, conviction
3. Confluence scoring across 7 pillars following Sebastian's institutional framework
4. Historical tracking showing how views evolved
5. Clean web dashboard accessible on mobile + desktop
6. All sources processed: text, PDFs, images, video transcripts

---

## Data Sources

### Current Collector Status (as of 2025-11-28)

| Source | Status | Method | Priority | Frequency |
|--------|--------|--------|----------|-----------|
| **Discord (Options Insight)** | ✅ **PRODUCTION READY** | discord.py-self (local) | HIGH | Real-time |
| **YouTube** | ✅ **PRODUCTION READY** | YouTube Data API v3 | Medium | Daily check |
| **Substack (Visser Labs)** | ✅ **PRODUCTION READY** | RSS feed | Medium | Weekly |
| **42 Macro** | ✅ **PRODUCTION READY** | Selenium (CloudFront bypass) | HIGH | Daily |
| **KT Technical Website** | ✅ **PRODUCTION READY** | Session-based auth | HIGH | Weekly (Sundays) |

**Future Enhancement**: Manual tweet input via dashboard (no Twitter API subscription).

---

### 1. Options Insight (Discord) - ✅ PRODUCTION READY
- **Authentication**: Sebastian's personal Discord account (user token)
- **Content Types**:
  - Text analysis from 6 channels
  - Chart images (IV vs spot, volatility surfaces)
  - PDFs with market summaries
  - Zoom/Webex video links with live analysis (HIGH VALUE - Imran's commentary)
- **Collection Method**: Local Python script using discord.py-self
- **Channels Monitored**:
  - macro-daily
  - spx-fixed-strike-vol
  - macro-weekly
  - crypto-weekly
  - vix-monitor
  - stock-trades
- **Schedule**: Runs locally on laptop (6am, 6pm via Task Scheduler)
- **Note**: Videos contain majority of alpha - transcripts are critical

### 2. YouTube - ✅ PRODUCTION READY
- **Channel IDs** (real, tested):
  - Peter Diamandis: UCCpNQKYvrnWQNjZprabMJlw
  - Jordi Visser Labs: UCSLOw8JrFTBb3qF-p4v0v_w
  - Forward Guidance: UCEOv-8wHvYC6mzsY2Gm5WcQ
  - 42 Macro: UCu0L0QCubkYD3Cd9jSdxTNQ
- **Content Types**: Long-form macro discussions, interviews, market analysis
- **Collection Method**: YouTube Data API v3 (official)
- **Test Results**: 40 videos collected (10 per channel)
- **Frequency**: Check daily, publish weekly

### 3. Substack (Visser Labs) - ✅ PRODUCTION READY
- **URL**: https://visserlabs.substack.com/
- **Collection Method**: RSS feed parsing (feedparser)
- **Content Types**: Weekly macro/crypto analysis articles
- **Test Results**: 20 articles collected successfully
- **Frequency**: Weekly publications

### 4. Twitter (@MelMattison1) - ✅ PRODUCTION READY
- **Account**: @MelMattison1 (Market analysis, macro trader, economic history)
- **Collection Method**: Official Twitter API v2 with `tweepy`
- **Content Types**: Trade setups, technical levels, macro commentary
- **Authentication**: Bearer Token (stored in `.env` as `TWITTER_BEARER_TOKEN`)
- **Status**: ✅ Thread-aware collection with media download
- **Test Results**: Thread reconstruction working, media downloaded
- **Frequency**: Daily monitoring
- **Note**: @KTTECHPRIVATE removed (content available via KT Technical website)

### 5. 42 Macro - ✅ PRODUCTION READY
- **URL**: https://app.42macro.com
- **Authentication**: Email/password (stored in `.env`)
- **Content Types**:
  - PDFs: "Around The Horn", "Macro Scouting Report"
  - Videos: "Macro Minute" daily videos (for future transcript harvesting)
  - KISS Model Portfolio signals (in weekly PDFs)
- **Collection Method**: Selenium + headless Chrome
- **Status**: ✅ Automatic PDF downloading working
- **Test Results**: Successfully downloaded 4 PDFs (Around The Horn, Macro Scouting Report)
- **Frequency**: Daily (morning notes), Weekly (reports)
- **Note**: "Leadoff Morning Note" requires premium tier subscription (locked)

### 6. KT Technical Analysis Website - ✅ PRODUCTION READY
- **URL**: https://kttechnicalanalysis.com/blog-feed/
- **Authentication**: Email/password (stored in `.env` as `KT_EMAIL`, `KT_PASSWORD`)
- **Content Types**:
  - Weekly blog posts with price chart images (CRITICAL)
  - Synopsis of stock/asset price action with Elliott Wave analysis
  - Technical levels, support/resistance zones
- **Collection Method**: Session-based authentication + individual post fetching
- **Status**: ✅ Full content + price chart images downloading
- **Test Results**: 10 blog posts collected, 3-4 chart images per post
- **Frequency**: Weekly (Sundays)
- **Note**: Price charts are CRITICAL - technical analysis meaningless without them

---

## Technical Architecture

### Tech Stack Decisions
- **Backend**: Python (FastAPI)
- **Database**: SQLite with full historical tracking
- **Frontend**: React or vanilla JS (clean, mobile-responsive)
- **Deployment**: Railway (Sebastian has subscription)
- **AI**: Claude API (Sonnet 4.5) for all analysis
- **Transcription**: OpenAI Whisper API for video content
- **Version Control**: GitHub with feature branch workflow

### Repository Structure
```
confluence/                    # Monorepo
├── docs/                      # All PRDs, planning docs
│   ├── CLAUDE.md             # This file
│   ├── PRD_MASTER.md         # Overall roadmap
│   ├── PRD-001.md            # Individual PRDs
│   └── ...
├── CHANGELOG.md              # Progress tracking
├── README.md                 # Project overview
│
├── agents/                    # AI Sub-agents
│   ├── __init__.py
│   ├── content_classifier.py
│   ├── transcript_harvester.py
│   ├── pdf_analyzer.py
│   ├── image_intelligence.py
│   ├── confluence_scorer.py
│   └── cross_reference.py
│
├── collectors/                # Data collection modules
│   ├── __init__.py
│   ├── discord_self.py       # Local laptop script
│   ├── macro42.py
│   ├── twitter_scraper.py
│   ├── youtube_api.py
│   └── substack_rss.py
│
├── backend/                   # Railway-deployed API
│   ├── app.py                # FastAPI main
│   ├── models.py             # Database models
│   ├── routes/
│   │   ├── collect.py        # Trigger collections
│   │   ├── analyze.py        # Run analysis
│   │   └── confluence.py     # Get confluence data
│   ├── scheduler.py          # Cron jobs (6am, 6pm)
│   └── utils/
│       ├── auth.py
│       ├── db.py
│       └── claude_api.py
│
├── database/
│   ├── schema.sql            # SQLite schema
│   ├── migrations/           # Schema version control
│   └── confluence.db         # Actual database
│
├── frontend/                  # Web dashboard
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── App.jsx
│   └── package.json
│
├── tests/                     # Test suites
│   ├── test_agents/
│   ├── test_collectors/
│   └── test_integration/
│
├── scripts/                   # Utility scripts
│   └── discord_local.py      # Runs on Sebastian's laptop
│
├── .github/
│   └── workflows/
│       └── tests.yml         # CI/CD pipeline
│
├── .gitignore
├── requirements.txt
└── railway.json              # Railway config
```

### Development Workflow

**⚠️ CRITICAL RULE: NEVER PUSH DIRECTLY TO MAIN BRANCH ⚠️**

**ALWAYS use feature branches. ALWAYS create pull requests. ONLY merge to main after tests pass.**

#### Mandatory Workflow Steps

1. **Feature Branches (REQUIRED)**
   - **ALWAYS** create a new feature branch for ANY changes
   - Branch naming: `feature/description` or `fix/description` or `update/description`
   - Examples: `feature/discord-collector`, `fix/authentication-bug`, `update/prd-004`
   - **NEVER, EVER commit directly to main branch**
   - **NEVER use `git push` when on main branch**

2. **Commits on Feature Branch**
   - Make frequent, logical commits on your feature branch
   - Reference issue numbers in commits (#1, #2, etc.)
   - Update CHANGELOG.md with meaningful changes

3. **Push Feature Branch to GitHub**
   - Push your feature branch: `git push -u origin <branch-name>`
   - Feature branches can be pushed freely

4. **Pull Requests (REQUIRED for all merges to main)**
   - Create a Pull Request from your feature branch to main
   - PR description should explain changes clearly
   - Wait for tests to pass (CI/CD pipeline)
   - **DO NOT merge until all tests pass**
   - Only merge via GitHub PR interface, never with direct push

5. **After Merge**
   - Switch back to main: `git checkout main`
   - Pull latest changes: `git pull`
   - Delete local feature branch: `git branch -d <branch-name>`

#### Example Workflow

```bash
# Step 1: Create feature branch
git checkout -b feature/add-discord-collector

# Step 2: Make changes, commit frequently
git add .
git commit -m "Add Discord collector implementation"

# Step 3: Push feature branch
git push -u origin feature/add-discord-collector

# Step 4: Create PR on GitHub (via web interface or gh CLI)
gh pr create --title "Add Discord Collector" --body "Implements PRD-004..."

# Step 5: Wait for tests to pass, then merge PR on GitHub

# Step 6: After PR is merged on GitHub
git checkout main
git pull
git branch -d feature/add-discord-collector
```

#### GitHub Issues
- Each PRD task tracked as Issue
- Issues grouped by Milestones
- Reference issues in commits and PRs

---

## AI Sub-Agent Architecture

**Philosophy**: Each "agent" is a Python module with a specialized Claude API call. No complex frameworks - clean, testable, transparent.

### Agent Implementation Status

| Agent | Status | Lines | Implementation |
|-------|--------|-------|----------------|
| Base Agent | ✅ Complete | 175 | Claude API integration, JSON parsing, schema validation |
| Content Classifier | ✅ Complete | 334 | Priority rules engine, routing logic, fallback classification |
| Transcript Harvester | ✅ Complete | 363 | Multi-platform video transcription, Whisper API |
| PDF Analyzer | ✅ Complete | 810 | PyPDF2/PyMuPDF, table extraction, report type detection |
| Image Intelligence | ✅ Complete | 450 | Claude Vision API, chart type detection, structured insights |
| Confluence Scorer | ✅ Complete | 490 | 7-pillar framework scoring, confidence calculations |
| Cross-Reference | ✅ Complete | 637 | Bayesian conviction updating, theme clustering |
| Transcript Chart Matcher | ✅ Complete | 336 | Cost optimization for 42 Macro videos |
| Visual Content Classifier | ✅ Complete | 380 | Image routing, lightweight classification |
| Cleanup Manager | ✅ Complete | 473 | Storage management, retention policies |

**Total: 4,456 lines across 10 agents - All production-ready**

### Agent Specifications

#### 1. Content Classifier Agent ✅ IMPLEMENTED
**Status**: Fully functional (334 lines)
**Purpose**: First-pass triage of all collected content
**Input**: Raw content (text, file path, URL)
**Output**:
```json
{
  "content_type": "video|pdf|image|text",
  "source": "42macro|discord|twitter|youtube|substack|kt_technical",
  "priority": "high|medium|low",
  "route_to": ["transcript_harvester", "pdf_analyzer"],
  "detected_topics": ["topic1", "topic2"],
  "confidence": 0.95
}
```
**Implementation**: Uses Claude API with priority rules and routing logic
**File**: `agents/content_classifier.py`

#### 2. Transcript Harvester Agent ✅ IMPLEMENTED
**Status**: Fully functional (363 lines)
**Purpose**: Convert video/audio to analyzed text
**Inputs**: Video URL (YouTube, Zoom, Webex, Twitter video)
**Process**:
1. Download video via yt-dlp
2. Extract audio → Whisper API transcription
3. Claude analysis of transcript
**Output**:
```json
{
  "transcript": "full text...",
  "key_themes": ["Fed pivot", "tech sector rotation"],
  "tickers_mentioned": ["SPY", "QQQ", "NVDA"],
  "sentiment": "bullish|bearish|neutral",
  "conviction": 0-10,
  "time_horizon": "1d|1w|1m|3m|6m+",
  "catalysts": ["FOMC meeting", "earnings"]
}
```
**Implementation**: Multi-platform support (YouTube, Zoom, Vimeo, Twitter)
**File**: `agents/transcript_harvester.py`

#### 3. PDF Analyzer Agent ✅ IMPLEMENTED
**Status**: Fully functional (810 lines)
**Purpose**: Extract structured insights from PDF research reports
**Process**:
1. Text extraction via PyPDF2 (primary) or PyMuPDF (fallback)
2. Image extraction for chart analysis
3. Table extraction when available
4. Claude analysis for themes, tickers, sentiment
**Features**:
- Report type detection (Around The Horn, Macro Scouting Report, Leadoff)
- Source-specific prompts (42macro, Discord)
- KISS Model portfolio positioning extraction
- Transcript-based chart prioritization (89% cost reduction)
**Output**: Key themes, market regime, positioning, tickers, valuations
**File**: `agents/pdf_analyzer.py`

#### 4. Image Intelligence Agent ✅ IMPLEMENTED
**Status**: Fully functional (450 lines)
**Purpose**: Interpret charts, graphs, volatility surfaces via Claude Vision
**Process**:
1. Base64 image encoding for API transmission
2. Claude Vision API for chart interpretation
3. Source-specific analysis (Discord volatility vs KT Technical)
**Features**:
- Support for PNG, JPG, JPEG, WEBP, GIF formats
- Volatility surface analysis (IV levels, term structure, skew)
- Elliott Wave identification for technical charts
- Support/resistance level extraction
**Output**: Image type, extracted text, interpretation, key levels, tickers
**File**: `agents/image_intelligence.py`

#### 5. Confluence Scorer Agent ✅ IMPLEMENTED
**Status**: Fully functional (490 lines)
**Purpose**: Score content against Sebastian's 7-pillar framework
**Input**: Analyzed content from other agents
**Scoring Rubric** (from Sebastian's macro_confluence_definition.md):
```
Core 5 Pillars (0-2 each):
1. Macro data & regime
2. Sector/company fundamentals
3. Valuation & capital cycle
4. Positioning/flows
5. Narrative/policy alignment

Hybrid-specific (0-2 each):
6. Price action / technical structure
7. Options/volatility surface

Confluence Threshold: ≥6-7/10 core + at least one hybrid pillar at 2/2
```
**Features**:
- Rigorous scoring with institutional-grade prompts
- Falsification criteria generation (specific, measurable)
- Variant view identification
- P&L mechanism extraction
**Output**:
```json
{
  "pillar_scores": {...},
  "core_total": 8,
  "total_score": 11,
  "meets_threshold": true,
  "confluence_level": "strong|medium|weak",
  "reasoning": {...},
  "falsification_criteria": ["If CPI >0.5% MoM", "If SPY breaks 5800"],
  "variant_view": "...",
  "p_and_l_mechanism": "..."
}
```
**File**: `agents/confluence_scorer.py`

#### 6. Cross-Reference Agent ✅ IMPLEMENTED
**Status**: Fully functional (637 lines)
**Purpose**: Find confluence patterns across sources
**Process**:
1. Extract themes from confluence-scored content
2. Cluster similar themes using Claude semantic similarity
3. Find cross-source confluence (2+ sources agree)
4. Bayesian updating with proper P(H|E) formula
5. Detect contradictions
**Features**:
- Source reliability weights (42macro: 0.9, Discord: 0.85, etc.)
- Conviction buckets (low/medium/high/table_pounding)
- Conviction trend tracking (rising/falling/stable)
- Historical theme tracking
**Output**:
```json
{
  "confluent_themes": [...],
  "contradictions": [...],
  "high_conviction_ideas": [...],
  "total_themes": 15,
  "confluent_count": 5,
  "high_conviction_count": 2
}
```
**File**: `agents/cross_reference.py`

---

## Confluence Framework

Sebastian's investment framework is based on institutional-grade macro analysis. Full definition in `/docs/macro_confluence_definition.md`.

### Core Principles
1. **Independence**: Signals must be truly independent, not same data restated
2. **Economic Coherence**: Clear causal chain from macro → cash flows → prices
3. **Variant View**: Must differ from market consensus (what's priced in)
4. **P&L Mechanism**: Explicit path to profit over defined horizon
5. **Falsification Criteria**: Know what would prove thesis wrong

### Scoring System
- **0 = Weak**: Story only, no evidence
- **1 = Medium**: Some evidence, but incomplete
- **2 = Strong**: Multiple independent indicators, clear mechanism

### Investor Type: Semi-Discretionary/Hybrid
Sebastian blends:
- Macro/thematic research
- Company-level fundamentals
- Technical analysis for timing
- Options structures for expression

**Decision Rule**: Only act if:
- Core score ≥6-7/10
- At least one hybrid pillar (price action OR options) scores 2/2
- Clear variant view articulated
- Explicit falsification criteria defined

---

## Special Technical Considerations

### Discord Local Script
**Challenge**: No bot permissions, must use Sebastian's logged-in session
**Solution**: 
- Python script using `discord.py-self` library
- Runs on Sebastian's laptop (Discord always running, auto-login on startup)
- Scheduled via Windows Task Scheduler or cron
- If laptop off during scheduled run, executes on next startup
- Uploads collected data to Railway API endpoint

**Data Collection**:
1. Monitor specified channels
2. Download text, images, PDFs
3. Extract Zoom/Webex links
4. Package as JSON
5. POST to Railway API `/ingest/discord`

### Video Transcription Priority
**Key Insight**: Video transcripts contain the REAL alpha, especially:
- Imran's Discord videos (Options Insight)
- Darius Dale's 42macro videos
- YouTube long-form discussions

**Quality Requirements**:
- Use Whisper API (not YouTube auto-captions alone)
- Preserve speaker attribution when possible
- Timestamp key moments
- Claude analysis must extract nuance, not just topics

### Bayesian Updating
**Implementation**:
- Store prior conviction scores for each theme
- When new evidence arrives, update belief
- Track confidence intervals over time
- Visualize conviction trends in dashboard

---

## User Experience Requirements

### Dashboard Features
1. **Today's View**: Latest analysis, confluence scores, urgent signals
2. **Theme Tracker**: Active investment themes, strength over time
3. **Source Browser**: Drill down into specific sources
4. **Confluence Matrix**: Heatmap showing pillar scores across ideas
5. **Historical View**: How themes evolved
6. **Manual Actions**: 
   - Trigger on-demand collection
   - Force re-analysis
   - Mark themes as "acted upon" or "invalidated"

### Mobile Experience
- Clean, readable on phone
- Quick access to high-conviction ideas
- Push notifications for high-priority confluence (future feature)

### Performance
- Dashboard loads <2 seconds
- Real-time updates when new data processed
- Handles 6 months of historical data smoothly

---

## Development Phases

### Phase 0: Setup (Day 1)
- GitHub Issues created
- Project structure initialized
- CHANGELOG.md started

### Phase 1: Foundation (Week 1)
- Database schema
- Basic collectors (no AI yet)
- Content Classifier Agent
- Test with real data from one source

### Phase 2: Intelligence Layer (Week 2)
- Build all 4 content analysis agents
- Unit tests for each
- Integration tests
- Process real research from all sources

### Phase 3: Confluence Engine (Week 3)
- Confluence Scorer Agent
- Cross-Reference Agent
- Bayesian tracking system
- Historical data pipeline

### Phase 4: Dashboard + Deploy (Week 4)
- Frontend dashboard
- Railway deployment
- End-to-end testing
- Documentation

---

## Testing Strategy

### Unit Tests
Each agent has isolated tests:
- Mock Claude API responses
- Test parsing logic
- Validate output schema

### Integration Tests
- Full pipeline: raw content → analyzed → scored
- Cross-agent communication
- Database persistence

### Manual Testing
Sebastian will test with:
- Recent 42macro reports (known content)
- Discord messages from last week
- YouTube videos he's watched

### CI/CD
GitHub Actions:
- Run tests on every PR
- Block merge if tests fail
- Deploy to Railway on main branch merge

---

## API Cost Estimates

### Claude API
- ~500 content items/day (across all sources)
- Average 1000 tokens input, 500 tokens output per analysis
- ~$30-50/month at current pricing

### Whisper API
- ~10 videos/day
- ~30 minutes average length
- ~$15-25/month

**Total Estimated**: $50-75/month (acceptable to Sebastian)

---

## Critical Success Factors

1. **Video Transcription Quality**: This is where alpha lives - must be excellent
2. **Confluence Scoring Accuracy**: Must match Sebastian's mental model
3. **Bayesian Updates**: Properly track conviction evolution
4. **Mobile UX**: Must be usable on phone for quick checks
5. **Reliability**: 6am/6pm runs must be bulletproof

---

## Future Enhancements (Post-MVP)

- Real-time Discord monitoring (WebSocket)
- Push notifications for high-conviction confluence
- Export to trading journal
- Backtesting: "What if I'd acted on 8/10 confluence ideas?"
- Multi-user support (share with trading partners)
- Integration with brokerage APIs for position tracking

---

## Key Technical Decisions Rationale

### Why Custom Agents (not LangGraph/CrewAI)?
- Sebastian is a beginner - simpler = better
- Full transparency for debugging
- No framework learning curve
- Easier to modify behavior

### Why SQLite (not Postgres)?
- Simpler setup for beginner
- Railway persistent storage works fine
- Query performance sufficient for this data volume
- Can migrate later if needed

### Why Railway (not Vercel/AWS)?
- Sebastian already has subscription
- Simple deployment
- Good for beginners
- Persistent storage included

### Why Monorepo?
- Simpler for Sebastian to manage
- Easier to see full picture
- Reduces context switching
- Better for vibe coding approach

---

## Contact & Credentials

**Credentials Storage**: `config/credentials.json` (encrypted, not in git)
```json
{
  "42macro": {"email": "...", "password": "..."},
  "twitter": {"session_token": "..."},
  "youtube_api": {"key": "..."},
  "claude_api": {"key": "..."},
  "whisper_api": {"key": "..."}
}
```

**Environment Variables** (Railway):
- `CLAUDE_API_KEY`
- `WHISPER_API_KEY`
- `YOUTUBE_API_KEY`
- `DATABASE_URL`
- `SECRET_KEY`

---

## Success Metrics (Post-Launch)

1. **Data Collection**: >95% success rate on scheduled runs
2. **Analysis Quality**: Sebastian validates 20 confluence scores, >90% match his judgment
3. **Time Saved**: Sebastian spends <30 min/day reviewing (vs 2+ hours manually)
4. **Conviction Clarity**: Can articulate thesis + confluence score for any active idea
5. **Acting on Ideas**: Tracks which high-confluence ideas led to profitable trades

---

## Notes for Future Claude Sessions

- Sebastian prefers concise explanations, bias toward action
- When stuck, build something simple and iterate
- Frequent commits > perfect code
- Test with real data early and often
- Sebastian will provide feedback on confluence scoring - adjust accordingly
- Discord transcript quality is CRITICAL - do not skip or abbreviate

---

**Last Updated**: 2025-11-28
**Project Start Date**: 2025-11-18
**MVP Status**: ✅ COMPLETE (~14,000 lines of production code)
**Current Phase**: Production ready - Integration testing and deployment
