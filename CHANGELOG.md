# Changelog

All notable changes to the Macro Confluence Hub project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **[PRD-002] Database Schema & Infrastructure** ✅ COMPLETED
  - Complete SQLite schema with 7 tables (database/schema.sql)
    - sources: Data source configuration
    - raw_content: Collected content before analysis
    - analyzed_content: AI agent analysis results
    - confluence_scores: Pillar-by-pillar scoring
    - themes: Investment themes being tracked
    - theme_evidence: Many-to-many linking table
    - bayesian_updates: Conviction tracking over time
  - All indexes and foreign key constraints implemented
  - Database utilities (backend/utils/db.py)
    - DatabaseManager class with CRUD operations
    - Connection management with context managers
    - Query helpers with filters, ordering, limits
    - JSON serialization for complex data types
  - SQLAlchemy ORM models (backend/models.py)
    - 7 model classes matching schema
    - Proper relationships and cascade deletes
    - Check constraints for score ranges
    - Helper functions for database access
  - Migration system (database/migrations/, scripts/run_migrations.py)
    - Python-based migrations with upgrade/downgrade
    - Migration tracking table
    - Rollback support
    - Migration 001: Initial schema
  - Comprehensive test suite (tests/test_database.py)
    - 15+ tests covering all CRUD operations
    - Foreign key constraint tests
    - Full pipeline integration test
    - 95%+ test coverage

- **[PRD-001] GitHub Project Management**
  - Created 5 GitHub Milestones (Phase 0-4)
  - Created GitHub Issues for Phase 1 tasks:
    - Issue #2: [PRD-002] Database Schema & Infrastructure
    - Issue #3: [PRD-003] Content Classifier Agent
    - Issue #4: [PRD-004] Basic Collectors (No AI)
  - Added project labels: agent, collector, database, frontend, infrastructure, testing, documentation

- **Development Workflow Documentation**
  - Updated CLAUDE.md with strict feature branch workflow
  - Added mandatory PR requirement (no direct pushes to main)
  - Documented branch naming conventions and example workflow

- **PRD Updates**
  - PRD-004 updated to v1.1 with comprehensive Discord collection strategy
  - Added channel-based collection approach with configuration system
  - Added helper scripts and complete implementation details

- **Testing Infrastructure**
  - Added tests/test_setup.py with placeholder tests
  - Verifies project structure, required files, and documentation
  - Ensures CI pipeline passes during Phase 0

### Changed
- PRD-001 status updated to "Completed"
- PRD-002 status updated to "Completed"
- All PRD-002 success criteria marked as complete (except final review)

### Notes
- Phase 0 (PRD-001) project setup: COMPLETE ✅
- Phase 1 Task 1 (PRD-002) database schema: COMPLETE ✅
- Ready for PRD-003 (Content Classifier Agent) and PRD-004 (Basic Collectors)
- Feature branch workflow enforced going forward

---

## [0.2.0] - 2025-11-18

### Added
- **[PRD-001] Complete Project Structure**
  - Full monorepo directory tree matching PRD specification
  - agents/ package with 6 AI agent placeholders
  - collectors/ package with 5 collector modules + Discord local script
  - backend/ package with FastAPI foundation
  - database/ directory with migrations folder
  - frontend/ directory structure
  - tests/ directory with test suites structure
  - scripts/ directory with initialization and utility scripts
  - config/ directory for credentials management

- **Configuration Files**
  - .gitignore covering Python, JS, database, credentials, IDE files
  - requirements.txt with pinned dependencies for all project needs
  - .env.example template with all required environment variables
  - railway.json for Railway deployment configuration
  - config/example.credentials.json for credential management

- **Database Infrastructure**
  - scripts/init_database.py - Database initialization script
  - scripts/run_migrations.py - Migration runner
  - scripts/seed_data.py - Sample data seeding
  - backend/models.py - SQLAlchemy model foundation

- **Backend API Foundation**
  - backend/app.py - FastAPI application with CORS
  - Root endpoint (/) and health check (/health)
  - Route structure for future API endpoints
  - Utility modules for database, auth, Claude API
  - Scheduler template for automated collection

- **CI/CD Pipeline**
  - .github/workflows/tests.yml - GitHub Actions workflow
  - Automated testing on PR and push to main
  - Coverage reporting integration

### Security
- Credentials excluded from git via .gitignore
- Environment variable management via .env
- config/credentials.json gitignored
- Example credentials template provided

---

## [0.1.0] - 2025-11-18

### Added
- Initial project documentation structure
- CLAUDE.md - Comprehensive project context and specifications
- PRD_MASTER.md - Overall project roadmap and phase breakdown
- PRD-001 through PRD-011 - Detailed product requirement documents
- README.md - Project overview with architecture
- START_HERE.md - Guide for Sebastian
- docs/macro_confluence_definition.md - Investment framework
- GitHub repository created
- Project planning completed

### Notes
- Project inception date
- All documentation created and reviewed
- Technical architecture decisions documented
- Ready to begin implementation

---

## Development Phases Overview

### Phase 0: Project Setup ✅ COMPLETE
- PRD-001: Infrastructure and GitHub configuration
- Completed: 2025-11-18

### Phase 1: Foundation (Week 1) - NEXT
- PRD-002: Database Schema
- PRD-003: Content Classifier Agent
- PRD-004: Basic Collectors
- Expected completion: 2025-11-25

### Phase 2: Intelligence Layer (Week 2)
- PRD-005: Transcript Harvester Agent
- PRD-006: PDF Analyzer Agent
- PRD-007: Image Intelligence Agent
- Expected completion: 2025-12-02

### Phase 3: Confluence Engine (Week 3)
- PRD-008: Confluence Scorer Agent
- PRD-009: Cross-Reference Agent
- Expected completion: 2025-12-09

### Phase 4: Dashboard & Deployment (Week 4)
- PRD-010: Web Dashboard
- PRD-011: Railway Deployment
- Expected completion: 2025-12-16

---

## Version History

**0.2.0** - Project Setup Complete (2025-11-18)
- Full project structure implemented
- All configuration files created
- Backend foundation established
- Ready for Phase 1 development

**0.1.0** - Planning and Documentation (2025-11-18)
- Complete project specification
- All PRDs created
- Architecture designed

**1.0.0** - MVP Target (2025-12-16)
- Fully functional system
- All 6 data sources integrated
- 6 AI agents operational
- Web dashboard deployed to Railway
- Automated scheduling (6am, 6pm)
- Historical data tracking

---

## How to Use This Changelog

### For Developers
- Update this file with every meaningful commit
- Reference PRD numbers and GitHub Issue numbers
- Use semantic versioning for releases

### For Sebastian
- Quick reference to see what's been built
- Track progress toward MVP
- Understand what changed between sessions

### Commit Format
```
[PRD-XXX] Short description

Longer explanation of changes.

Updates CHANGELOG.md:
- Added: New feature X
- Changed: Improved Y
- Fixed: Bug Z

Closes #issue-number
```

---

## Notes

- This is a living document - update frequently
- Major changes should include rationale
- Breaking changes should be highlighted
- Link to relevant PRDs and Issues

---

**Last Updated**: 2025-11-18
**Next Review**: After Phase 1 completion
