# PRD-045: Collection Monitoring & Alerting

**Status**: Not Started
**Priority**: Critical
**Estimated Complexity**: Medium
**Target**: January 2026

## Overview

Implement comprehensive monitoring and alerting for the collection pipeline to prevent silent failures like the 1-month YouTube transcription outage. This PRD addresses the #1 risk identified in the product review: "Collection Pipeline Failures Go Undetected."

## Problem Statement

### The YouTube Incident (January 2026)

YouTube video collection appeared to work for ~1 month while transcription silently failed:
1. YouTube collector on Railway fetched video metadata (new videos appeared in database)
2. Videos were queued for async transcription via `asyncio.create_task()`
3. Background TranscriptHarvesterAgent failed (Whisper API errors / yt-dlp failures)
4. Failures were logged but NOT tracked in database
5. CollectionRun status only tracked collection success, not transcription completion
6. GitHub Actions saw "success" (HTTP 200) and reported no errors
7. **Result**: 86 videos accumulated in backlog; critical insights missed

### Root Causes

1. **Async transcription with no tracking**: Failures don't propagate
2. **No per-source health dashboard**: Can't see which sources are healthy at a glance
3. **Success metric misalignment**: "Collection successful" ≠ "Content usable for synthesis"
4. **No alerting**: User must actively check, not notified of issues

## Goals

1. Track per-video transcription status in database
2. Expose per-source health via API and dashboard
3. Alert on consecutive collection failures
4. Integrate transcription status into existing dashboard

## Implementation Plan

### 45.1 Database Models

**File**: `backend/models.py`

**Model 1**: `TranscriptionStatus`
```python
class TranscriptionStatus(Base):
    """Track individual video transcription status."""
    __tablename__ = "transcription_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey("raw_content.id", ondelete="CASCADE"), nullable=False, unique=True)

    status = Column(String(20), nullable=False, default="pending")
    # Values: pending, processing, completed, failed, skipped

    error_message = Column(Text)  # If failed, why
    retry_count = Column(Integer, default=0)
    last_attempt_at = Column(DateTime)
    completed_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    content = relationship("RawContent", back_populates="transcription_status")
```

**Model 2**: `SourceHealth`
```python
class SourceHealth(Base):
    """Cached health metrics per source."""
    __tablename__ = "source_health"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String(50), nullable=False, unique=True)

    last_collection_at = Column(DateTime)
    last_collection_status = Column(String(20))  # success, partial, failed
    last_transcription_at = Column(DateTime)  # For video sources

    items_collected_24h = Column(Integer, default=0)
    items_transcribed_24h = Column(Integer, default=0)
    errors_24h = Column(Integer, default=0)

    consecutive_failures = Column(Integer, default=0)
    is_stale = Column(Boolean, default=False)  # No new content in 48+ hours

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 45.2 Transcription Tracking Integration

**File**: `backend/routes/collect.py`

**Changes to YouTube collection flow**:

```python
# Before: Async fire-and-forget
async def collect_youtube(...):
    # ... video metadata saved ...
    asyncio.create_task(_transcribe_video_async(video_id))  # Silent failure

# After: Track status in database
async def collect_youtube(...):
    # ... video metadata saved ...

    # Create transcription status record
    status = TranscriptionStatus(
        content_id=content.id,
        status="pending"
    )
    db.add(status)
    await db.commit()

    # Queue transcription (still async, but now tracked)
    asyncio.create_task(_transcribe_video_with_tracking(content.id, status.id))

async def _transcribe_video_with_tracking(content_id: int, status_id: int):
    async with AsyncSessionLocal() as db:
        status = await db.get(TranscriptionStatus, status_id)
        status.status = "processing"
        status.last_attempt_at = datetime.utcnow()
        await db.commit()

        try:
            result = await _transcribe_video_sync(content_id, db)
            status.status = "completed"
            status.completed_at = datetime.utcnow()
        except Exception as e:
            status.status = "failed"
            status.error_message = str(e)
            status.retry_count += 1
            logger.error(f"Transcription failed for content {content_id}: {e}")
        finally:
            await db.commit()
```

### 45.3 Health API Endpoints

**File**: `backend/routes/health.py` (new file)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health/sources` | GET | Get health status for all sources |
| `/api/health/sources/{source}` | GET | Get detailed health for specific source |
| `/api/health/transcription` | GET | Get transcription queue status |
| `/api/health/alerts` | GET | Get active alerts |
| `/api/health/alerts/{id}/acknowledge` | POST | Acknowledge an alert |

**Response for `/api/health/sources`**:
```json
{
  "sources": {
    "youtube": {
      "status": "degraded",
      "last_collection": "2026-01-19T10:00:00Z",
      "last_transcription": "2026-01-18T15:00:00Z",
      "items_24h": 5,
      "transcribed_24h": 2,
      "pending_transcription": 3,
      "errors_24h": 2,
      "consecutive_failures": 0,
      "is_stale": false
    },
    "discord": {
      "status": "healthy",
      "last_collection": "2026-01-19T08:00:00Z",
      "items_24h": 23,
      "consecutive_failures": 0,
      "is_stale": false
    },
    "42macro": {
      "status": "stale",
      "last_collection": "2026-01-17T12:00:00Z",
      "items_24h": 0,
      "consecutive_failures": 0,
      "is_stale": true
    }
    // ... other sources
  },
  "overall_status": "degraded",
  "alerts": [
    {
      "id": 1,
      "type": "transcription_backlog",
      "source": "youtube",
      "message": "3 videos pending transcription for >24 hours",
      "created_at": "2026-01-19T09:00:00Z"
    }
  ]
}
```

### 45.4 Alerting System

**File**: `backend/services/alerting.py` (new file)

**Alert Types**:
| Type | Trigger | Severity |
|------|---------|----------|
| `collection_failed` | 2+ consecutive collection failures | Critical |
| `transcription_backlog` | Pending transcriptions >24h old | High |
| `source_stale` | No new content in 48+ hours | Medium |
| `error_spike` | >5 errors in 24h for a source | High |

**Alert Delivery**:
1. **Phase 1** (this PRD): Store alerts in database + show on dashboard
2. **Phase 2** (future): Email/Slack webhook notifications

**Alert Model**:
```python
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(50), nullable=False)
    source = Column(String(50))
    severity = Column(String(20), nullable=False)  # critical, high, medium, low
    message = Column(Text, nullable=False)

    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String(100))

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # Auto-dismiss after this time
```

**Alert Check Job** (runs on GitHub Actions or Railway cron):
```python
async def check_and_create_alerts():
    """Check all sources and create alerts as needed."""
    async with AsyncSessionLocal() as db:
        for source in MONITORED_SOURCES:
            health = await get_source_health(source, db)

            # Check consecutive failures
            if health.consecutive_failures >= 2:
                await create_alert_if_not_exists(
                    db,
                    alert_type="collection_failed",
                    source=source,
                    severity="critical",
                    message=f"{source} has failed {health.consecutive_failures} consecutive collections"
                )

            # Check staleness
            if health.is_stale:
                await create_alert_if_not_exists(
                    db,
                    alert_type="source_stale",
                    source=source,
                    severity="medium",
                    message=f"No new content from {source} in 48+ hours"
                )

            # Check transcription backlog (for video sources)
            if source in VIDEO_SOURCES:
                pending = await get_pending_transcriptions(source, older_than_hours=24, db=db)
                if pending > 0:
                    await create_alert_if_not_exists(
                        db,
                        alert_type="transcription_backlog",
                        source=source,
                        severity="high",
                        message=f"{pending} videos pending transcription for >24 hours"
                    )
```

### 45.5 Dashboard Integration

**File**: `frontend/index.html`

**Health Widget** (add to Overview tab header):
```html
<div id="source-health-widget" class="health-widget">
    <div class="health-indicator" id="health-overall">
        <span class="health-dot"></span>
        <span class="health-label">Sources</span>
    </div>
    <div class="health-dropdown" id="health-dropdown">
        <!-- Populated by JS -->
    </div>
</div>
```

**File**: `frontend/js/health.js` (new file)

**HealthManager**:
- `init()` - Fetch health on page load
- `fetchSourceHealth()` - Call `/api/health/sources`
- `updateHealthWidget(data)` - Update indicator colors
- `showHealthDropdown()` - Show detailed per-source status
- `renderAlerts(alerts)` - Show active alerts in dropdown

**Visual Indicators**:
- 🟢 Healthy: All sources operational, no alerts
- 🟡 Degraded: Some sources have issues
- 🔴 Critical: Collection failures or major backlog

### 45.6 GitHub Actions Integration

**File**: `.github/workflows/scheduled-collection.yml`

**Add health check step after collection**:
```yaml
- name: Check collection health
  if: always()  # Run even if collection failed
  run: |
    response=$(curl -s -u ${{ secrets.AUTH_USER }}:${{ secrets.AUTH_PASS }} \
      https://confluence-production-a32e.up.railway.app/api/health/sources)

    overall=$(echo $response | jq -r '.overall_status')
    if [ "$overall" = "critical" ]; then
      echo "::error::Collection health is CRITICAL"
      # Future: Send Slack/email notification
    fi

- name: Check transcription status
  if: github.event.schedule == '0 12 * * *'  # Only on noon run
  run: |
    response=$(curl -s -u ${{ secrets.AUTH_USER }}:${{ secrets.AUTH_PASS }} \
      https://confluence-production-a32e.up.railway.app/api/health/transcription)

    pending=$(echo $response | jq -r '.pending_count')
    if [ "$pending" -gt 10 ]; then
      echo "::warning::$pending videos pending transcription"
    fi
```

### 45.7 Heartbeat Expansion

**File**: `backend/routes/heartbeat.py`

**Add heartbeats for all sources** (currently only Discord):
- Add `MACRO42_THRESHOLD_HOURS = 26` (runs every 12h, generous buffer)
- Add `YOUTUBE_THRESHOLD_HOURS = 26`
- Add `SUBSTACK_THRESHOLD_HOURS = 26`
- Add `KT_THRESHOLD_HOURS = 26`

**New endpoint**:
```python
@router.get("/heartbeat/status")
async def get_all_heartbeat_status(db: AsyncSession = Depends(get_async_db)):
    """Get heartbeat status for all monitored services."""
    # Returns status for each source with last_seen and is_overdue
```

### 45.8 Synchronous Transcription Mode (C4)

**Problem**: Current async transcription queue (`asyncio.create_task()`) allows failures to go undetected.

**Solution**: Add synchronous transcription mode that runs inline after collection.

**File**: `backend/routes/collect.py`

```python
SYNC_TRANSCRIPTION = os.getenv("SYNC_TRANSCRIPTION", "false").lower() == "true"

async def collect_youtube(...):
    # ... video metadata saved ...

    # Create transcription status record
    status = TranscriptionStatus(content_id=content.id, status="pending")
    db.add(status)
    await db.commit()

    if SYNC_TRANSCRIPTION:
        # Synchronous: Run inline, errors propagate to collection response
        try:
            await _transcribe_video_with_tracking(content.id, status.id)
        except Exception as e:
            # Mark collection as partial success
            return {"status": "partial", "error": f"Transcription failed: {e}"}
    else:
        # Async: Queue for background processing (tracked)
        asyncio.create_task(_transcribe_video_with_tracking(content.id, status.id))

    return {"status": "success"}
```

**Benefits of Sync Mode**:
- Errors propagate immediately to GitHub Actions
- Collection status reflects actual usability
- Simpler debugging (no background task mysteries)

**Tradeoffs**:
- Slower collection (blocks on transcription)
- API timeout risk for long videos

**Recommendation**: Enable sync mode (`SYNC_TRANSCRIPTION=true`) for reliability.

---

## Definition of Done

### Database Models
- [ ] `TranscriptionStatus` model added to `backend/models.py`
- [ ] Model tracks: status, error_message, retry_count, last_attempt_at, completed_at
- [ ] Status enum: pending, processing, completed, failed, skipped
- [ ] Foreign key to `raw_content` with CASCADE delete
- [ ] `SourceHealth` model added with health metrics per source
- [ ] `Alert` model added for alerting system
- [ ] All models have proper indexes

### Transcription Tracking
- [ ] `_transcribe_video_with_tracking()` function created
- [ ] Status updated to "processing" before transcription starts
- [ ] Status updated to "completed" or "failed" after transcription
- [ ] Error messages captured in `error_message` column
- [ ] Retry count incremented on failures
- [ ] `SYNC_TRANSCRIPTION` env var controls sync vs async mode

### Health API
- [ ] `backend/routes/health.py` file created
- [ ] `GET /api/health/sources` returns all source health
- [ ] `GET /api/health/sources/{source}` returns specific source detail
- [ ] `GET /api/health/transcription` returns transcription queue status
- [ ] `GET /api/health/alerts` returns active alerts
- [ ] `POST /api/health/alerts/{id}/acknowledge` acknowledges alert
- [ ] All endpoints require authentication

### Alerting System
- [ ] `backend/services/alerting.py` file created
- [ ] `check_and_create_alerts()` function detects issues
- [ ] Alert types: collection_failed, transcription_backlog, source_stale, error_spike
- [ ] Alerts auto-created when thresholds exceeded
- [ ] Alert acknowledgment updates `is_acknowledged` flag
- [ ] Duplicate alerts prevented (check existing before creating)

### Dashboard UI
- [ ] Health widget added to Overview tab header
- [ ] Widget shows 🟢/🟡/🔴 indicator based on overall status
- [ ] Click widget expands dropdown with per-source status
- [ ] Each source shows: status, last_collection, items_24h, errors_24h
- [ ] Active alerts shown in dropdown
- [ ] Alert acknowledge button works
- [ ] Health refreshes on page load

### GitHub Actions Integration
- [ ] Health check step added to scheduled-collection.yml
- [ ] Step runs even if collection fails (`if: always()`)
- [ ] Step outputs error if overall_status is "critical"
- [ ] Step outputs warning if transcription backlog > 10
- [ ] Step outputs info showing source health summary

### Heartbeat Expansion
- [ ] Heartbeat thresholds defined for all sources
- [ ] `GET /api/heartbeat/status` returns all source heartbeats
- [ ] Dashboard shows heartbeat status in health widget

### Testing
- [ ] Unit tests pass (`tests/test_prd045_monitoring.py`)
- [ ] Integration tests pass
- [ ] Playwright UI tests pass (`tests/playwright/prd045-health.spec.js`)

### Documentation
- [ ] CLAUDE.md updated with health monitoring info
- [ ] PRD moved to `/docs/archived/` on completion

---

## Testing Requirements

**Unit Tests** (`tests/test_prd045_monitoring.py`):
- Test TranscriptionStatus state transitions (pending → processing → completed/failed)
- Test SourceHealth calculations (items_24h, errors_24h, is_stale)
- Test alert creation logic for each alert type
- Test staleness detection (48h threshold)
- Test duplicate alert prevention
- Test sync vs async transcription mode
- Test error message capture

**Integration Tests**:
- Test health API returns correct data for each source
- Test transcription tracking updates status correctly
- Test alerts created when thresholds exceeded
- Test alert acknowledgment persists
- Test GitHub Actions health check output

**UI Tests** (`tests/playwright/prd045-health.spec.js`):
- Health widget renders in Overview tab
- Widget shows correct color based on status
- Click widget expands dropdown
- Dropdown shows all sources with status
- Source status shows correct metrics
- Alerts display in dropdown
- Acknowledge button works
- Dropdown closes on outside click
- Mobile responsive

## Dependencies

- PRD-034 (Observability Foundation) - Existing heartbeat infrastructure
- PRD-035 (Database Modernization) - Async sessions

## Future Enhancements (Out of Scope)

1. **Email/Slack notifications** - Webhook-based alerting
2. **Automatic retry** - Retry failed transcriptions on schedule
3. **Prometheus metrics** - Time-series monitoring
4. **Grafana dashboard** - Dedicated monitoring UI

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Alert fatigue from too many alerts | Start with conservative thresholds; add acknowledgment |
| Health endpoint adds latency | Cache health data; update async every 5 min |
| GitHub Actions visibility limited | Consider Railway cron job for critical checks |
