# Development & Research Files

This directory contains all non-production code, documentation, and development artifacts.

## Directory Structure

### `scripts/`
Test and utility scripts for development and debugging:
- `test_*.py` - Component test scripts
- `debug_*.py` - Debugging utilities
- `run_*.py` - Manual execution scripts

### `tests/`
Unit and integration tests using pytest.

### `docs/`
Product Requirements Documents (PRDs) and design documentation:
- Feature specifications
- Architecture decisions
- Implementation plans

### `logs/`
Application logs and debug output from development runs.

### `downloads/`
Downloaded content cache (PDFs, images, etc.) - gitignored.

### `temp/`
Temporary files generated during processing - gitignored.

### `test_output/`
Output from test runs and debugging sessions.

### `debug/`
Debug artifacts and exploratory analysis.

---

## Key Files

- **CHANGELOG.md** - Detailed changelog of all features and fixes
- **START_HERE.md** - Developer onboarding guide
- **pytest.ini** - Pytest configuration
- **scheduler.log** - Scheduler execution logs

---

## Production Code

Production code remains in the root directory:
- `agents/` - AI analysis agents
- `backend/` - FastAPI application
- `collectors/` - Data collection modules
- `frontend/` - Web dashboard
- `config/` - Configuration
- `database/` - SQLite database

See root `README.md` for production deployment instructions.
