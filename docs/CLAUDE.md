# Macro Confluence Hub - Project Context

## Project Overview

A personal investment research aggregation and analysis system that collects macro and market analysis from multiple paid sources, analyzes content for confluence across Sebastian's investment framework, and provides a unified dashboard for decision-making.

**Core Capability**: Bayesian confluence tracking across 7 investment pillars (macro data, fundamentals, valuation, positioning, policy, price action, options/volatility) to build conviction in investment ideas.

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

### 1. 42 Macro (app.42macro.com)
- **Authentication**: Email/password login
- **Content Types**: 
  - PDFs: "Leadoff Morning Note", "Around The Horn", "Macro Scouting Report"
  - Videos: "Macro Minute" daily videos with transcripts
  - KISS Model Portfolio signals and Excel data
- **Collection Method**: Authenticated web scraping, S3 PDF downloads
- **Frequency**: Daily (morning notes), Weekly (reports)

### 2. Options Insight (Discord)
- **Authentication**: Sebastian's personal Discord account (always logged in)
- **Content Types**:
  - Text analysis in #stocks-chat, #crypto-weekly, #macro-daily
  - Chart images (IV vs spot, volatility surfaces)
  - PDFs with market summaries
  - Zoom/Webex video links with live analysis (HIGH VALUE - Imran's commentary)
- **Collection Method**: Local Python script using discord.py-self
- **Key Channels**: 
  - stocks-chat (pre-market analysis)
  - crypto-weekly 
  - macro-daily
  - spx-fixed-strike-vol
  - vix-monitor
- **Note**: Videos contain majority of alpha - transcripts are critical

### 3. KT Technical Analysis
- **Twitter Account**: @KTTECHPRIVATE
- **Website**: Daily/weekly guidance (authentication TBD)
- **Content Types**: Trade setups, technical levels, day/swing trade ideas
- **Collection Method**: Twitter scraping (no API), website scraping

### 4. YouTube Channels
- **Accounts**:
  - https://www.youtube.com/@peterdiamandis
  - https://www.youtube.com/@JordiVisserLabs
  - https://www.youtube.com/@ForwardGuidanceBW
  - https://www.youtube.com/@42Macro
- **Content Types**: Long-form macro discussions, interviews, market analysis
- **Collection Method**: YouTube API for metadata + transcripts

### 5. Additional Twitter
- **Accounts**: @MelMattison1
- **Collection Method**: Web scraping

### 6. Substack
- **Account**: https://visserlabs.substack.com/
- **Collection Method**: RSS feed parsing

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

### Agent Specifications

#### 1. Content Classifier Agent
**Purpose**: First-pass triage of all collected content
**Input**: Raw content (text, file path, URL)
**Output**: 
```json
{
  "content_type": "video|pdf|image|text",
  "source": "42macro|discord|twitter|youtube|substack",
  "priority": "high|medium|low",
  "route_to": ["transcript_harvester", "pdf_analyzer"],
  "metadata": {...}
}
```
**Claude Prompt Focus**: Pattern recognition, content type detection

#### 2. Transcript Harvester Agent
**Purpose**: Convert video/audio to analyzed text
**Inputs**: Video URL (YouTube, Zoom, Webex, Twitter video)
**Process**:
1. Download video (if needed)
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

#### 3. PDF Analyzer Agent
**Purpose**: Extract structured insights from PDF research reports
**Process**:
1. Text extraction (pypdf2)
2. Table extraction (camelot/tabula)
3. Claude analysis for themes
**Output**: Similar structure to transcript harvester

#### 4. Image Intelligence Agent
**Purpose**: Interpret charts, graphs, volatility surfaces
**Process**:
1. OCR if text-heavy
2. Claude vision API for chart interpretation
**Output**: Structured data about what chart shows

#### 5. Confluence Scorer Agent
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
**Output**:
```json
{
  "pillar_scores": {
    "macro": 2,
    "fundamentals": 1,
    "valuation": 2,
    "positioning": 1,
    "policy": 2,
    "price_action": 2,
    "options_vol": 1
  },
  "total_score": 11,
  "core_score": 8,
  "meets_threshold": true,
  "reasoning": "Strong macro data support with clear capital cycle...",
  "falsification_criteria": ["If CPI comes in >0.5% MoM", "If SPY breaks 5800"]
}
```

#### 6. Cross-Reference Agent
**Purpose**: Find confluence patterns across sources
**Process**:
1. Compare themes across time windows
2. Identify when 2+ sources agree on same thesis
3. Flag contradictions
4. Bayesian updating of prior beliefs
**Output**:
```json
{
  "confluent_themes": [
    {
      "theme": "Tech sector rotation imminent",
      "supporting_sources": ["42macro ATH", "Options Insight Imran", "KT Technical"],
      "confidence": 0.85,
      "first_mentioned": "2025-04-15",
      "strength_over_time": [0.3, 0.5, 0.7, 0.85]
    }
  ],
  "contradictions": [...],
  "high_conviction_ideas": [...]
}
```

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

**Last Updated**: 2025-11-18
**Project Start Date**: 2025-11-18
**Target MVP Completion**: 2025-12-16 (4 weeks)
