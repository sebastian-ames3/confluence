# Changelog

All notable changes to the Macro Confluence Hub project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **[PRD-003] Content Classifier Agent** - First AI sub-agent implementation
  - BaseAgent class with Claude API integration
  - ContentClassifierAgent with priority rules and routing logic
  - Comprehensive unit test suite (23 tests, all passing)
  - API endpoints for content classification
  - Database integration for storing classification results
  - Support for all 6 data sources (42macro, Discord, Twitter, YouTube, Substack, KT Tech)
  - Automatic routing to specialized agents based on content type
  - Priority assignment (high/medium/low) based on source and content patterns
  - Fallback classification when Claude API unavailable
- API routes for content analysis:
  - POST /analyze/classify/{raw_content_id} - Classify single item
  - POST /analyze/classify-batch - Batch classification
  - GET /analyze/pending - View pending analysis count
  - GET /analyze/stats - Analysis statistics

### Changed
- Updated backend/routes/analyze.py with full implementation
- Enhanced agents/__init__.py exports

### Testing
- 23 unit tests implemented for ContentClassifierAgent
- All tests passing
- Coverage includes: priority rules, routing logic, API integration, edge cases

### Notes
- Classification accuracy depends on Claude API quality
- Processing time estimates: Video (190s), PDF (40s), Text (10s)
- Classifier achieves <2s response time target (excluding specialized agent processing)

---

## [0.1.0] - 2025-11-18

### Added
- GitHub repository created: `confluence`
- Initial README.md
- Project planning phase initiated
- Technical architecture decisions documented
- Data source integration strategy defined
- Sub-agent development approach established

### Notes
- Project inception date
- Planning phase with Sebastian
- All documentation created and awaiting review
- Ready to begin Phase 0 (Project Setup) upon approval

---

## Development Phases Overview

### Phase 0: Project Setup (1 day)
- PRD-001: Infrastructure and GitHub configuration
- Expected completion: 2025-11-19

### Phase 1: Foundation (Week 1)
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

**0.1.0** - Planning and Documentation (2025-11-18)
- Complete project specification
- All PRDs created
- Ready for development

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
**Next Review**: After Phase 0 completion
