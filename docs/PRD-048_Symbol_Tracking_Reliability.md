# PRD-048: Symbol Tracking Reliability

**Status**: Not Started
**Priority**: Medium
**Estimated Complexity**: Medium
**Target**: January 2026

## Overview

Improve the reliability of PRD-039's Symbol Tracking feature by adding staleness validation on read operations and concurrency protection for refresh operations.

## Problem Statement

The product review identified these issues with Symbol Tracking:

1. **M3: Symbol Staleness Only Checked on Refresh** - `symbols.py` calculates staleness only during refresh operations, not when reading data. Users may see stale data without warning.

2. **M4: No Concurrency Lock on Symbol Updates** - `symbols.py:296-347` has a race condition where simultaneous refresh requests can corrupt data or create duplicate levels.

## Goals

1. Always show staleness warning when data is old
2. Prevent race conditions during symbol refresh
3. Improve overall data consistency

---

## Implementation Plan

### 48.1 Staleness Validation on Read (M3)

**Problem**: Symbol data can be days old, but the API only calculates staleness during refresh.

**File**: `backend/routes/symbols.py`

**Current Code** (staleness only on refresh):
```python
@router.get("/api/symbols/{symbol}")
async def get_symbol_detail(symbol: str, db: AsyncSession = Depends(get_async_db)):
    state = await db.get(SymbolState, symbol.upper())
    if not state:
        raise HTTPException(404, "Symbol not found")

    return {
        "symbol": state.symbol,
        "direction": state.direction,
        "last_updated": state.last_updated,
        # No staleness info!
    }
```

**Fixed Code**:
```python
from datetime import datetime, timedelta

STALENESS_THRESHOLD_HOURS = int(os.getenv("SYMBOL_STALENESS_HOURS", "48"))

def calculate_staleness(last_updated: datetime) -> dict:
    """Calculate staleness info for symbol data."""
    if not last_updated:
        return {
            "is_stale": True,
            "hours_since_update": None,
            "staleness_message": "Never updated"
        }

    hours_since = (datetime.utcnow() - last_updated).total_seconds() / 3600

    return {
        "is_stale": hours_since > STALENESS_THRESHOLD_HOURS,
        "hours_since_update": round(hours_since, 1),
        "staleness_message": (
            f"Data is {round(hours_since)}h old - may be outdated"
            if hours_since > STALENESS_THRESHOLD_HOURS
            else None
        )
    }

@router.get("/api/symbols/{symbol}")
async def get_symbol_detail(symbol: str, db: AsyncSession = Depends(get_async_db)):
    state = await db.get(SymbolState, symbol.upper())
    if not state:
        raise HTTPException(404, "Symbol not found")

    staleness = calculate_staleness(state.last_updated)

    return {
        "symbol": state.symbol,
        "direction": state.direction,
        "last_updated": state.last_updated,
        **staleness  # Include is_stale, hours_since_update, staleness_message
    }

@router.get("/api/symbols")
async def get_all_symbols(db: AsyncSession = Depends(get_async_db)):
    """Get all tracked symbols with staleness info."""
    result = await db.execute(select(SymbolState))
    states = result.scalars().all()

    return {
        "symbols": [
            {
                "symbol": state.symbol,
                "direction": state.direction,
                "last_updated": state.last_updated,
                **calculate_staleness(state.last_updated)
            }
            for state in states
        ],
        "staleness_threshold_hours": STALENESS_THRESHOLD_HOURS
    }
```

**Dashboard UI Update**:

**File**: `frontend/js/symbols.js`

```javascript
function renderSymbolCard(symbol) {
    const stalenessClass = symbol.is_stale ? 'stale' : 'fresh';
    const stalenessWarning = symbol.staleness_message
        ? `<div class="staleness-warning">${symbol.staleness_message}</div>`
        : '';

    return `
        <div class="symbol-card ${stalenessClass}">
            <div class="symbol-header">
                <span class="symbol-name">${symbol.symbol}</span>
                <span class="symbol-direction ${symbol.direction}">${symbol.direction}</span>
            </div>
            ${stalenessWarning}
            <div class="symbol-meta">
                Last updated: ${formatRelativeTime(symbol.last_updated)}
            </div>
        </div>
    `;
}
```

**CSS**:
```css
.symbol-card.stale {
    border-left: 3px solid var(--warning-color);
    opacity: 0.8;
}

.staleness-warning {
    font-size: var(--text-sm);
    color: var(--warning-color);
    padding: var(--spacing-xs);
    background: var(--warning-bg);
    border-radius: var(--radius-sm);
    margin-top: var(--spacing-xs);
}
```

---

### 48.2 Concurrency Lock on Symbol Updates (M4)

**Problem**: Simultaneous refresh requests can cause race conditions.

**File**: `backend/routes/symbols.py`

**Current Code** (race condition):
```python
@router.post("/api/symbols/{symbol}/refresh")
async def refresh_symbol(symbol: str, db: AsyncSession = Depends(get_async_db)):
    # Delete existing levels
    await db.execute(delete(SymbolLevel).where(SymbolLevel.symbol == symbol))

    # Extract new levels
    new_levels = await extractor.extract_levels(symbol)

    # Insert new levels
    for level in new_levels:
        db.add(level)

    # If another request runs between delete and insert, data is corrupted
    await db.commit()
```

**Fixed Code** (with database-level locking):
```python
from sqlalchemy import select, delete, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
import asyncio

# In-memory lock for non-PostgreSQL databases
_symbol_locks = {}

def get_symbol_lock(symbol: str) -> asyncio.Lock:
    """Get or create a lock for a symbol."""
    if symbol not in _symbol_locks:
        _symbol_locks[symbol] = asyncio.Lock()
    return _symbol_locks[symbol]

@router.post("/api/symbols/{symbol}/refresh")
async def refresh_symbol(symbol: str, db: AsyncSession = Depends(get_async_db)):
    symbol = symbol.upper()

    # Acquire lock for this symbol
    lock = get_symbol_lock(symbol)

    if lock.locked():
        # Another refresh is in progress
        return {
            "status": "already_refreshing",
            "message": f"Refresh already in progress for {symbol}"
        }

    async with lock:
        try:
            # Start transaction
            async with db.begin():
                # For PostgreSQL: Use SELECT FOR UPDATE to lock the row
                state = await db.execute(
                    select(SymbolState)
                    .where(SymbolState.symbol == symbol)
                    .with_for_update()
                )
                state = state.scalar_one_or_none()

                if not state:
                    raise HTTPException(404, f"Symbol {symbol} not found")

                # Delete existing levels within transaction
                await db.execute(
                    delete(SymbolLevel).where(SymbolLevel.symbol == symbol)
                )

                # Extract new levels
                extractor = SymbolLevelExtractor()
                new_levels = await extractor.extract_levels(symbol, db)

                # Insert new levels
                for level_data in new_levels:
                    level = SymbolLevel(symbol=symbol, **level_data)
                    db.add(level)

                # Update state timestamp
                state.last_updated = datetime.utcnow()
                state.level_count = len(new_levels)

                # Commit transaction (all or nothing)
                await db.commit()

            return {
                "status": "success",
                "symbol": symbol,
                "levels_extracted": len(new_levels),
                "last_updated": state.last_updated.isoformat()
            }

        except Exception as e:
            logger.error(f"Symbol refresh failed for {symbol}: {e}")
            raise HTTPException(500, f"Refresh failed: {str(e)}")
```

**Alternative: Optimistic Locking**

If database-level locking is too heavy, use optimistic locking with version numbers:

```python
class SymbolState(Base):
    # ... existing fields ...
    version = Column(Integer, default=0, nullable=False)

@router.post("/api/symbols/{symbol}/refresh")
async def refresh_symbol(symbol: str, db: AsyncSession = Depends(get_async_db)):
    # Get current version
    state = await db.get(SymbolState, symbol.upper())
    if not state:
        raise HTTPException(404, "Symbol not found")

    original_version = state.version

    # ... do extraction ...

    # Update with version check (optimistic lock)
    result = await db.execute(
        update(SymbolState)
        .where(
            SymbolState.symbol == symbol,
            SymbolState.version == original_version  # Only update if version unchanged
        )
        .values(
            last_updated=datetime.utcnow(),
            version=original_version + 1
        )
    )

    if result.rowcount == 0:
        # Another request modified the data
        raise HTTPException(
            409,
            "Conflict: Symbol was modified by another request. Please retry."
        )

    await db.commit()
```

---

## Definition of Done

### Staleness Validation (M3)
- [ ] `calculate_staleness()` helper function created
- [ ] `SYMBOL_STALENESS_HOURS` env var added (default 48)
- [ ] `GET /api/symbols` returns staleness info for each symbol
- [ ] `GET /api/symbols/{symbol}` returns staleness info
- [ ] Response includes: is_stale, hours_since_update, staleness_message
- [ ] Dashboard displays staleness warning for stale symbols
- [ ] Stale symbols visually distinguished (opacity, border color)

### Concurrency Lock (M4)
- [ ] In-memory lock mechanism implemented for symbol refresh
- [ ] Concurrent refresh returns "already_refreshing" status
- [ ] Database transaction wraps delete + insert operations
- [ ] SELECT FOR UPDATE used for PostgreSQL
- [ ] Optimistic locking fallback for SQLite
- [ ] Race condition eliminated (verified by test)

### Testing
- [ ] Unit tests pass (`tests/test_prd048_symbol_reliability.py`)
- [ ] Integration tests pass
- [ ] Playwright UI tests pass (`tests/playwright/prd048-symbols.spec.js`)
- [ ] Concurrent refresh test passes

### Documentation
- [ ] CLAUDE.md updated with symbol reliability info
- [ ] PRD moved to `/docs/archived/` on completion

---

## Testing Requirements

**Unit Tests** (`tests/test_prd048_symbol_reliability.py`):

```python
class TestStalenessCalculation:
    def test_fresh_data(self):
        last_updated = datetime.utcnow() - timedelta(hours=1)
        result = calculate_staleness(last_updated)
        assert result["is_stale"] is False
        assert result["staleness_message"] is None

    def test_stale_data(self):
        last_updated = datetime.utcnow() - timedelta(hours=72)
        result = calculate_staleness(last_updated)
        assert result["is_stale"] is True
        assert "72h old" in result["staleness_message"]

    def test_never_updated(self):
        result = calculate_staleness(None)
        assert result["is_stale"] is True
        assert result["staleness_message"] == "Never updated"

    def test_threshold_boundary(self):
        # Exactly at threshold should not be stale
        last_updated = datetime.utcnow() - timedelta(hours=48)
        result = calculate_staleness(last_updated)
        assert result["is_stale"] is False

        # Just over threshold should be stale
        last_updated = datetime.utcnow() - timedelta(hours=49)
        result = calculate_staleness(last_updated)
        assert result["is_stale"] is True


class TestConcurrencyLock:
    @pytest.mark.asyncio
    async def test_concurrent_refresh_blocked(self):
        """Second refresh should return already_refreshing."""
        # Start first refresh (slow)
        task1 = asyncio.create_task(slow_refresh("SPX"))

        # Try second refresh immediately
        await asyncio.sleep(0.1)  # Let first acquire lock
        response = await client.post("/api/symbols/SPX/refresh")

        assert response.json()["status"] == "already_refreshing"

        await task1  # Clean up

    @pytest.mark.asyncio
    async def test_sequential_refresh_succeeds(self):
        """Sequential refreshes should both succeed."""
        response1 = await client.post("/api/symbols/SPX/refresh")
        assert response1.json()["status"] == "success"

        response2 = await client.post("/api/symbols/SPX/refresh")
        assert response2.json()["status"] == "success"

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self):
        """If extraction fails, no levels should be deleted."""
        # Get initial level count
        initial = await client.get("/api/symbols/SPX")
        initial_count = initial.json().get("level_count", 0)

        # Mock extraction to fail
        with patch('agents.symbol_level_extractor.extract_levels') as mock:
            mock.side_effect = Exception("Extraction failed")

            response = await client.post("/api/symbols/SPX/refresh")
            assert response.status_code == 500

        # Level count should be unchanged
        after = await client.get("/api/symbols/SPX")
        assert after.json().get("level_count", 0) == initial_count


class TestAPIResponses:
    def test_get_symbols_includes_staleness(self):
        response = client.get("/api/symbols")
        data = response.json()

        for symbol in data["symbols"]:
            assert "is_stale" in symbol
            assert "hours_since_update" in symbol

    def test_get_symbol_detail_includes_staleness(self):
        response = client.get("/api/symbols/SPX")
        data = response.json()

        assert "is_stale" in data
        assert "hours_since_update" in data
```

**Integration Tests**:
- Test staleness calculation with various timestamps
- Test concurrent refresh handling
- Test transaction rollback on extraction failure
- Test API responses include staleness info

**UI Tests** (`tests/playwright/prd048-symbols.spec.js`):
- Stale symbols show warning banner
- Stale symbols have visual distinction (opacity, border)
- Refresh button disabled when refresh in progress
- "Already refreshing" message shown for concurrent refresh
- Fresh symbols don't show warning
- Staleness threshold configurable (if UI exposes setting)

---

## Dependencies

- PRD-039 (Symbol Tracking) - Base symbol infrastructure
- PRD-035 (Database Modernization) - Async sessions

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| In-memory lock doesn't work across multiple workers | Use database-level locking for production |
| SELECT FOR UPDATE not supported in SQLite | Use optimistic locking as fallback |
| Staleness threshold too aggressive | Default to 48h; make configurable |
