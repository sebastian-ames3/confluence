# PRD-035: Database Modernization

**Status**: Complete
**Priority**: Critical
**Estimated Complexity**: High

## Overview

Migrated from SQLite to PostgreSQL-ready architecture and implemented async database sessions to fix the sync-in-async anti-pattern that blocks the event loop.

## Goals

1. Eliminate SQLite locking issues during concurrent operations ✅
2. Enable true async database operations in FastAPI routes ✅
3. Add proper connection pooling for production workloads ✅
4. Provide migration path with rollback capability ✅

## Implementation

### 35.1 Async SQLAlchemy Session Support ✅

**Files modified:**
- `backend/models.py`
- `requirements.txt`

**Changes:**
- Added `aiosqlite`, `asyncpg`, and `greenlet` to requirements.txt
- Created async engine with PostgreSQL connection pooling
- Created `AsyncSessionLocal` session factory
- Created `get_async_db()` dependency for FastAPI routes
- Fixed Railway URL format (postgres:// → postgresql://)
- Graceful fallback when async dependencies not installed

### 35.2 Route Migration to Async Sessions ✅

**Files modified:**
- `backend/routes/heartbeat.py`
- `backend/routes/search.py`

**Pattern for migration:**
```python
# Before (sync)
@router.get("/items")
async def get_items(db: Session = Depends(get_db)):
    items = db.query(Item).filter(...).all()
    return items

# After (async)
from sqlalchemy import select
from backend.models import get_async_db, AsyncSession

@router.get("/items")
async def get_items(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Item).where(...))
    items = result.scalars().all()
    return items
```

### 35.3 PostgreSQL Migration Script ✅

**Files created:**
- `scripts/migrate_to_postgres.py`

**Usage:**
```bash
# Export SQLite data to JSON files
python scripts/migrate_to_postgres.py --export

# Import JSON data to PostgreSQL
python scripts/migrate_to_postgres.py --import

# Verify migration (compare row counts)
python scripts/migrate_to_postgres.py --verify

# Full migration (export + import + verify)
python scripts/migrate_to_postgres.py --full
```

### 35.4 Legacy DatabaseManager Deprecation ✅

**Files modified:**
- `backend/utils/db.py`

**Changes:**
- Added deprecation warning to DatabaseManager class
- Updated module docstring with migration guidance
- Created ServiceHeartbeat ORM model to replace raw SQL

## Testing

33 unit tests in `tests/test_prd035_database.py`:
- Async session support tests
- Route migration verification tests
- Migration script tests
- DatabaseManager deprecation tests
- Model integration tests

## Definition of Done

- [x] **35.1 Async Session Support**
  - [x] `aiosqlite` and `asyncpg` added to requirements.txt
  - [x] `AsyncSessionLocal` created in models.py
  - [x] `get_async_db()` dependency available
  - [x] Works with both SQLite and PostgreSQL URLs
  - [x] Graceful fallback when deps not installed

- [x] **35.2 Route Migration**
  - [x] heartbeat.py migrated to async ORM
  - [x] search.py migrated to async ORM
  - [x] Pattern documented for future migrations

- [x] **35.3 PostgreSQL Migration Script**
  - [x] Export functionality (SQLite → JSON)
  - [x] Import functionality (JSON → PostgreSQL)
  - [x] Verification functionality
  - [x] Full migration mode

- [x] **35.4 Legacy Cleanup**
  - [x] ServiceHeartbeat ORM model created
  - [x] DatabaseManager marked deprecated with warning

- [x] **Tests**
  - [x] 33 unit tests pass
  - [x] Tests work without async deps installed

## Notes

- Other routes (dashboard.py, themes.py, etc.) still use sync sessions for backwards compatibility
- These can be migrated incrementally using the same pattern
- The async dependencies (aiosqlite, asyncpg) will be installed on Railway
- Full PostgreSQL migration requires Railway PostgreSQL addon provisioning
