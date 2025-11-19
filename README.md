# Macro Confluence Hub

> Personal investment research aggregation and analysis system that automatically collects macro analysis from multiple premium sources, uses AI to extract insights, and surfaces high-conviction ideas through confluence scoring.

[![Status](https://img.shields.io/badge/status-planning-yellow)](https://github.com/sebastianames/confluence)
[![License](https://img.shields.io/badge/license-Private-red)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)

---

## 🎯 Problem Statement

As an active investor, I subscribe to multiple premium research services costing $1000s/month:
- 42 Macro (macro analysis, KISS model)
- Options Insight (Discord community with daily vol analysis)
- KT Technical Analysis (day/swing trade setups)
- Multiple YouTube channels and Twitter accounts

**Current Pain**: Spending 2+ hours/day manually reviewing content, trying to identify confluence across sources, tracking how views evolve over time.

**Solution**: Automated system that collects, analyzes, scores content against an institutional-grade investment framework, and surfaces high-conviction ideas in <30 minutes/day.

---

## ✨ Features

### Data Collection
- 🤖 Automated collection from 6+ sources (6am, 6pm, on-demand)
- 📄 PDFs, videos, images, text posts all supported
- 🎥 Video transcription using Whisper API
- 🔐 Secure credential management

### AI Analysis
- 6 specialized AI sub-agents (Content Classifier, Transcript Harvester, PDF Analyzer, Image Intelligence, Confluence Scorer, Cross-Reference)
- Claude API for sophisticated content analysis
- Extracts themes, tickers, sentiment, conviction levels
- Identifies falsification criteria for each thesis

### Confluence Scoring
- 7-pillar investment framework (institutional-grade)
- Scores: Macro, Fundamentals, Valuation, Positioning, Policy, Price Action, Options/Vol
- Clear thresholds for actionable conviction (≥6-7/10 core + strong hybrid pillar)
- Bayesian updating as new evidence arrives

### Dashboard
- Mobile-responsive web interface
- Today's View: High-conviction ideas at a glance
- Theme Tracker: Monitor active investment ideas over time
- Source Browser: Drill into specific sources
- Confluence Matrix: Visual heatmap of pillar scores
- Historical View: See how themes evolved

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Data Sources                            │
│  42macro │ Discord │ Twitter │ YouTube │ Substack │ KT Tech │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Raw Collectors                            │
│  Web Scrapers │ Discord Script │ YouTube API │ RSS Parser   │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Content Classifier                         │
│           Routes to appropriate agents                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ├──────┬─────────┬──────────┬────────────┐
         ▼      ▼         ▼          ▼            ▼
   ┌──────┐ ┌─────┐ ┌────────┐ ┌────────┐ ┌───────────┐
   │ PDF  │ │Video│ │ Image  │ │ Text   │ │  Simple   │
   │Agent │ │Agent│ │ Agent  │ │Analysis│ │  Archive  │
   └──┬───┘ └──┬──┘ └───┬────┘ └───┬────┘ └─────┬─────┘
      │        │         │          │            │
      └────────┴─────────┴──────────┴────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Confluence Scorer   │
              │   (7 Pillars)        │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Cross-Reference     │
              │  & Bayesian Updates  │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │    SQLite Database   │
              │  (Historical Data)   │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │    Web Dashboard     │
              │  (Mobile + Desktop)  │
              └──────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend, if using React)
- SQLite3
- Railway account (for deployment)
- **ffmpeg** (for video/audio processing)
  - Windows: `choco install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html)
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

### Installation

```bash
# Clone repository
git clone https://github.com/sebastianames/confluence.git
cd confluence

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys and credentials

# Initialize database
python scripts/init_database.py

# Run migrations
python scripts/run_migrations.py

# Seed sample data (optional)
python scripts/seed_data.py

# Start backend
uvicorn backend.app:app --reload

# In another terminal, start frontend
cd frontend
python -m http.server 8000
```

Open `http://localhost:8000` in your browser.

---

## 📊 Development Status

### Phase 0: Project Setup ⏳
- [x] Documentation created
- [ ] GitHub Issues configured
- [ ] Directory structure initialized
- [ ] CI/CD pipeline setup

### Phase 1: Foundation (Week 1) 📅
- [ ] Database schema implemented
- [ ] Content Classifier Agent built
- [ ] Basic collectors functional

### Phase 2: Intelligence Layer (Week 2) 📅
- [ ] Transcript Harvester Agent
- [ ] PDF Analyzer Agent
- [ ] Image Intelligence Agent

### Phase 3: Confluence Engine (Week 3) 📅
- [ ] Confluence Scorer Agent
- [ ] Cross-Reference Agent
- [ ] Bayesian tracking system

### Phase 4: Dashboard & Deploy (Week 4) 📅
- [ ] Web dashboard complete
- [ ] Railway deployment
- [ ] Production validation

**Target MVP Completion**: December 16, 2025

---

## 📚 Documentation

- [**CLAUDE.md**](docs/CLAUDE.md) - Complete project context and specifications
- [**PRD_MASTER.md**](docs/PRD_MASTER.md) - Overall roadmap and phase breakdown
- [**PRD-001 to PRD-011**](docs/) - Detailed product requirements
- [**CHANGELOG.md**](CHANGELOG.md) - Project progress tracking

### Key Documents
- **Confluence Framework**: See `docs/macro_confluence_definition.md` for the institutional-grade investment framework
- **Sub-Agent Architecture**: See CLAUDE.md for detailed agent specifications
- **Database Schema**: See PRD-002 for complete schema design

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/test_agents/
pytest tests/test_collectors/

# Run with coverage
pytest --cov=. --cov-report=html

# Run integration tests
pytest tests/test_integration/
```

---

## 🔐 Security

### Credentials Management
- Never commit credentials to git
- Use environment variables for sensitive data
- Credentials stored in `config/credentials.json` (gitignored)
- Railway env vars for production

### API Keys Required
- Claude API (Anthropic)
- Whisper API (OpenAI)
- YouTube Data API v3 (Google)
- 42 Macro credentials
- Discord user token (for local script)
- Twitter session token

---

## 📈 Cost Estimates

### Monthly Operational Costs
- **Claude API**: ~$40 (500 analyses/day)
- **Whisper API**: ~$20 (10 videos/day)
- **YouTube API**: Free (within quota limits)
- **Railway Hosting**: Included in subscription

**Total**: ~$60/month (within budget)

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite (with migration path to Postgres)
- **ORM**: SQLAlchemy
- **Scheduling**: APScheduler / schedule library

### AI & Analysis
- **LLM**: Claude Sonnet 4.5 (Anthropic)
- **Transcription**: Whisper API (OpenAI)
- **Image Analysis**: Claude Vision API

### Frontend
- **Framework**: Vanilla JavaScript (or React, TBD)
- **Charts**: Chart.js or D3.js
- **Styling**: CSS3 (mobile-first)

### Infrastructure
- **Hosting**: Railway
- **Version Control**: GitHub
- **CI/CD**: GitHub Actions

---

## 🤝 Contributing

This is a personal project, but if you're interested in building something similar:

1. Fork the repository
2. Read through the PRDs in `/docs`
3. Check out the confluence framework in `docs/macro_confluence_definition.md`
4. Build your own version!

---

## 📝 Development Workflow

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/PRD-002-database-schema

# Make changes and commit frequently
git add .
git commit -m "[PRD-002] Implement database schema

- Created schema.sql with all tables
- Added indexes for performance
- Implemented migration system

Updates CHANGELOG.md

Closes #5"

# Push to GitHub
git push origin feature/PRD-002-database-schema

# Create Pull Request
# Tests run automatically via GitHub Actions
# Merge after tests pass
```

### Issue Tracking
- Each PRD task becomes a GitHub Issue
- Issues grouped by Milestones (Phases)
- Labels: `agent`, `collector`, `database`, `frontend`, `infrastructure`, `testing`, `bug`, `documentation`

---

## 🎓 Learning Resources

If you're new to any of these technologies:

- **FastAPI**: https://fastapi.tiangolo.com/tutorial/
- **SQLAlchemy**: https://docs.sqlalchemy.org/en/20/tutorial/
- **Claude API**: https://docs.anthropic.com/
- **Railway**: https://docs.railway.app/

---

## 📊 Project Stats

- **Lines of Code**: TBD (post-development)
- **Test Coverage**: Target 90%+
- **API Endpoints**: ~15
- **AI Agents**: 6
- **Data Sources**: 6+
- **Database Tables**: 7

---

## 🙏 Acknowledgments

- **42 Macro** - Darius Dale's institutional-grade macro research
- **Options Insight** - Imran Lakha's options and volatility analysis
- **KT Technical Analysis** - Technical trade setups and guidance
- **Claude (Anthropic)** - AI assistance in building this project

---

## 📧 Contact

**Sebastian Ames**
- GitHub: [@sebastianames](https://github.com/sebastianames)
- Project: [confluence](https://github.com/sebastianames/confluence)

---

## 📜 License

Private project - All rights reserved.

---

## 🗺️ Roadmap

### MVP (v1.0) - December 2025
- [x] Project planning and documentation
- [ ] All 6 collectors operational
- [ ] 6 AI agents functional
- [ ] Confluence scoring implemented
- [ ] Web dashboard deployed
- [ ] Automated scheduling (6am, 6pm)

### Post-MVP (v1.1+)
- [ ] Real-time Discord monitoring (WebSocket)
- [ ] Push notifications for high-conviction ideas
- [ ] Mobile app (React Native)
- [ ] Position tracking integration
- [ ] Backtesting framework
- [ ] Multi-user support
- [ ] Export to trading journal

### Future Considerations (v2.0+)
- [ ] Integration with brokerage APIs
- [ ] Automated trade execution (with safeguards)
- [ ] Custom research source additions
- [ ] Advanced Bayesian modeling
- [ ] Predictive analytics

---

## ❓ FAQ

**Q: Why SQLite instead of Postgres?**  
A: Simplicity for MVP. Can migrate later if needed.

**Q: Why custom agents instead of LangChain/CrewAI?**  
A: Transparency, simplicity, easier for beginners to understand and modify.

**Q: Can this be used for other types of research?**  
A: Yes! The framework is adaptable to any domain requiring multi-source confluence analysis.

**Q: What if a data source changes its format?**  
A: Collectors are modular - update the specific collector without affecting others.

**Q: How accurate is the confluence scoring?**  
A: Target >90% alignment with manual analysis. Will be validated extensively with real data.

---

**Built with 🧠 by Sebastian Ames**  
**Last Updated**: 2025-11-18
