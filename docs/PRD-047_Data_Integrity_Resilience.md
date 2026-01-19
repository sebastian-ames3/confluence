# PRD-047: Data Integrity & Resilience

**Status**: Not Started
**Priority**: High
**Estimated Complexity**: Low
**Target**: January 2026

## Overview

Address data integrity issues that can cause runtime errors or poor user experience. This PRD covers null safety for database fields and timeout handling for long-running operations.

## Problem Statement

The product review identified these issues:

1. **H5: Missing Null Checks for analysis_result** - Code at `synthesis.py:837` and `dashboard.py` accesses `.analysis_result` without null guards, causing crashes when content hasn't been analyzed yet
2. **M2: No Timeout on Synthesis Generation** - `synthesis.py:252-462` can block until FastAPI timeout (60s default) with no user feedback

## Goals

1. Add null guards for all `.analysis_result` accesses
2. Add explicit timeout to synthesis generation with user-friendly error
3. Improve overall defensive coding patterns

---

## Implementation Plan

### 47.1 Null Safety for analysis_result (H5)

**Problem**: `AnalyzedContent.analysis_result` is nullable, but code accesses it without checks.

**Locations to Fix**:

| File | Line | Current Code | Issue |
|------|------|--------------|-------|
| `synthesis.py` | ~837 | `analyzed.analysis_result[:500]` | Crashes if None |
| `dashboard.py` | ~various | `item.analysis_result.get(...)` | Crashes if None |
| `search.py` | ~various | `content.analysis_result` | May be None |

**File**: `backend/routes/synthesis.py`

**Before**:
```python
# Line ~837
preview = analyzed.analysis_result[:500] if analyzed.analysis_result else ""
```

**After** (comprehensive fix):
```python
def safe_get_analysis_result(analyzed_content, max_length: int = None) -> dict:
    """Safely get analysis_result with null handling."""
    if not analyzed_content or not analyzed_content.analysis_result:
        return {}

    result = analyzed_content.analysis_result
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            return {"raw": result[:max_length] if max_length else result}

    return result

def safe_get_analysis_preview(analyzed_content, max_length: int = 500) -> str:
    """Safely get a preview of analysis_result."""
    if not analyzed_content or not analyzed_content.analysis_result:
        return "[Not analyzed]"

    result = analyzed_content.analysis_result
    if isinstance(result, dict):
        result = json.dumps(result)

    return result[:max_length] if len(result) > max_length else result
```

**File**: `backend/routes/dashboard.py`

```python
# Safe access pattern
def get_analysis_field(content, field: str, default=None):
    """Safely get a field from analysis_result."""
    if not content or not content.analysis_result:
        return default
    if isinstance(content.analysis_result, dict):
        return content.analysis_result.get(field, default)
    return default

# Usage
sentiment = get_analysis_field(item, "sentiment", "neutral")
themes = get_analysis_field(item, "themes", [])
```

**File**: `backend/routes/search.py`

```python
# Add null check before accessing
results = []
for content in query_results:
    if content.analysis_result:
        results.append({
            "id": content.id,
            "analysis": content.analysis_result,
            ...
        })
    else:
        results.append({
            "id": content.id,
            "analysis": None,
            "status": "not_analyzed"
        })
```

---

### 47.2 Synthesis Generation Timeout (M2)

**Problem**: Synthesis generation can take 30-60 seconds with no timeout, blocking the API.

**File**: `backend/routes/synthesis.py`

**Current Code**:
```python
@router.post("/synthesis/generate")
async def generate_synthesis(...):
    # ... setup ...
    result = agent.analyze_v3(content_items, older_content, time_window)
    # Can block for 60+ seconds with no timeout
```

**Fixed Code**:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

SYNTHESIS_TIMEOUT_SECONDS = int(os.getenv("SYNTHESIS_TIMEOUT", "120"))
executor = ThreadPoolExecutor(max_workers=2)

@router.post("/synthesis/generate")
async def generate_synthesis(...):
    # ... setup ...

    try:
        # Run synthesis with timeout
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(
                executor,
                lambda: agent.analyze_v3(content_items, older_content, time_window)
            ),
            timeout=SYNTHESIS_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        logger.error(f"Synthesis generation timed out after {SYNTHESIS_TIMEOUT_SECONDS}s")
        raise HTTPException(
            status_code=504,
            detail={
                "error": "synthesis_timeout",
                "message": f"Synthesis generation timed out after {SYNTHESIS_TIMEOUT_SECONDS} seconds. Try reducing the time window or content volume.",
                "timeout_seconds": SYNTHESIS_TIMEOUT_SECONDS
            }
        )

    # ... rest of function ...
```

**Alternative: Background Task with Polling**

For very long syntheses, consider a background task pattern:

```python
@router.post("/synthesis/generate")
async def generate_synthesis_async(...):
    """Start synthesis generation as background task."""
    task_id = str(uuid.uuid4())

    # Create pending synthesis record
    pending = Synthesis(
        status="generating",
        task_id=task_id,
        started_at=datetime.utcnow()
    )
    db.add(pending)
    await db.commit()

    # Start background task
    asyncio.create_task(_generate_synthesis_background(task_id, ...))

    return {
        "status": "generating",
        "task_id": task_id,
        "poll_url": f"/api/synthesis/status/{task_id}"
    }

@router.get("/synthesis/status/{task_id}")
async def get_synthesis_status(task_id: str):
    """Check status of synthesis generation."""
    synthesis = db.query(Synthesis).filter(Synthesis.task_id == task_id).first()
    if not synthesis:
        raise HTTPException(404, "Task not found")

    return {
        "status": synthesis.status,  # generating, completed, failed
        "progress": synthesis.progress,  # 0-100
        "result": synthesis.synthesis_response if synthesis.status == "completed" else None,
        "error": synthesis.error_message if synthesis.status == "failed" else None
    }
```

**Dashboard UI Update** (if using background task):

```javascript
async function generateSynthesis() {
    const response = await fetch('/api/synthesis/generate', { method: 'POST', ... });
    const data = await response.json();

    if (data.status === 'generating') {
        showProgressIndicator();
        pollForCompletion(data.task_id);
    }
}

async function pollForCompletion(taskId) {
    const interval = setInterval(async () => {
        const response = await fetch(`/api/synthesis/status/${taskId}`);
        const data = await response.json();

        if (data.status === 'completed') {
            clearInterval(interval);
            hideProgressIndicator();
            displaySynthesis(data.result);
        } else if (data.status === 'failed') {
            clearInterval(interval);
            hideProgressIndicator();
            showError(data.error);
        } else {
            updateProgress(data.progress);
        }
    }, 2000);  // Poll every 2 seconds
}
```

---

## Definition of Done

### Null Safety (H5)
- [ ] `safe_get_analysis_result()` helper function created
- [ ] `safe_get_analysis_preview()` helper function created
- [ ] `get_analysis_field()` helper function created
- [ ] `synthesis.py` uses safe accessors for analysis_result
- [ ] `dashboard.py` uses safe accessors for analysis_result
- [ ] `search.py` uses safe accessors for analysis_result
- [ ] `mcp/server.py` uses safe accessors for analysis_result
- [ ] No unchecked `.analysis_result` accesses remain in codebase
- [ ] Grep verification: `grep -r "\.analysis_result\[" --include="*.py"` returns 0 results

### Synthesis Timeout (M2)
- [ ] `SYNTHESIS_TIMEOUT` environment variable added (default 120s)
- [ ] `generate_synthesis()` wrapped with asyncio.wait_for()
- [ ] Timeout returns 504 with user-friendly message
- [ ] Timeout logged server-side
- [ ] Dashboard handles timeout gracefully (shows retry option)

### Testing
- [ ] Unit tests pass (`tests/test_prd047_data_integrity.py`)
- [ ] Integration tests pass
- [ ] Playwright UI tests pass (`tests/playwright/prd047-resilience.spec.js`)

### Documentation
- [ ] CLAUDE.md updated with data integrity patterns
- [ ] PRD moved to `/docs/archived/` on completion

---

## Testing Requirements

**Unit Tests** (`tests/test_prd047_data_integrity.py`):

```python
class TestSafeAnalysisAccess:
    def test_safe_get_analysis_result_with_none(self):
        content = Mock(analysis_result=None)
        result = safe_get_analysis_result(content)
        assert result == {}

    def test_safe_get_analysis_result_with_dict(self):
        content = Mock(analysis_result={"sentiment": "bullish"})
        result = safe_get_analysis_result(content)
        assert result["sentiment"] == "bullish"

    def test_safe_get_analysis_result_with_json_string(self):
        content = Mock(analysis_result='{"sentiment": "bullish"}')
        result = safe_get_analysis_result(content)
        assert result["sentiment"] == "bullish"

    def test_safe_get_analysis_preview_with_none(self):
        content = Mock(analysis_result=None)
        preview = safe_get_analysis_preview(content)
        assert preview == "[Not analyzed]"

    def test_safe_get_analysis_preview_truncates(self):
        content = Mock(analysis_result="x" * 1000)
        preview = safe_get_analysis_preview(content, max_length=100)
        assert len(preview) == 100

    def test_get_analysis_field_with_none_content(self):
        result = get_analysis_field(None, "sentiment", "neutral")
        assert result == "neutral"

    def test_get_analysis_field_with_missing_key(self):
        content = Mock(analysis_result={"themes": []})
        result = get_analysis_field(content, "sentiment", "neutral")
        assert result == "neutral"


class TestSynthesisTimeout:
    @pytest.mark.asyncio
    async def test_synthesis_timeout_returns_504(self):
        # Mock slow synthesis
        with patch('agents.synthesis_agent.SynthesisAgent.analyze_v3') as mock:
            mock.side_effect = lambda *args: time.sleep(200)

            response = await client.post("/api/synthesis/generate", ...)
            assert response.status_code == 504
            assert "timeout" in response.json()["detail"]["error"]

    @pytest.mark.asyncio
    async def test_synthesis_completes_within_timeout(self):
        # Mock fast synthesis
        with patch('agents.synthesis_agent.SynthesisAgent.analyze_v3') as mock:
            mock.return_value = {"version": "3.0", ...}

            response = await client.post("/api/synthesis/generate", ...)
            assert response.status_code == 200


class TestNoUncheckedAnalysisAccess:
    def test_no_direct_analysis_result_subscript(self):
        """Verify no code uses .analysis_result[ directly."""
        import subprocess
        result = subprocess.run(
            ['grep', '-r', r'\.analysis_result\[', '--include=*.py', 'backend/'],
            capture_output=True, text=True
        )
        assert result.stdout == "", f"Found unsafe access: {result.stdout}"
```

**Integration Tests**:
- Test dashboard loads with content that has null analysis_result
- Test search returns results even when some content not analyzed
- Test synthesis timeout triggers correctly
- Test timeout error displayed in dashboard

**UI Tests** (`tests/playwright/prd047-resilience.spec.js`):
- Dashboard loads without error when analysis_result is null
- Search results show "Not analyzed" for null content
- Synthesis timeout shows user-friendly error
- Retry button appears after timeout
- Progress indicator shown during synthesis (if using background task)

---

## Dependencies

- Existing synthesis infrastructure
- asyncio (standard library)

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Timeout too short for large syntheses | Default to 120s; make configurable |
| Helper functions add overhead | Negligible; safer code is worth it |
| Background task adds complexity | Optional enhancement; basic timeout is sufficient |
