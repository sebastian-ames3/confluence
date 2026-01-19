# PRD-046: Security Hardening Phase 2

**Status**: Not Started
**Priority**: High
**Estimated Complexity**: Low
**Target**: January 2026

## Overview

Address remaining security vulnerabilities identified in the product review. This PRD covers SQL injection prevention, error message sanitization, and rate limiting on write endpoints.

## Problem Statement

The product review identified these security issues:

1. **M1: SQL Injection via ilike()** - `synthesis.py:800-802` uses `.ilike()` with user input without proper escaping
2. **M5: Sensitive Data in Error Responses** - `app.py:104-118` global exception handler exposes full stack traces including potential API keys
3. **H6: Missing Rate Limits on Write Endpoints** - `/collect/discord`, `/collect/42macro`, `/analyze/classify-batch` lack rate limiting

While this is a single-user tool, these fixes follow security best practices and prevent accidental data leaks.

## Goals

1. Prevent SQL injection in search/filter queries
2. Redact sensitive data from error responses
3. Add rate limiting to all mutation endpoints

---

## Implementation Plan

### 46.1 SQL Injection Prevention (M1)

**File**: `backend/routes/synthesis.py`

**Current Code** (vulnerable):
```python
# Line 800-802
query = query.filter(
    Synthesis.synthesis_response.ilike(f"%{focus_topic}%")
)
```

**Fixed Code**:
```python
from backend.utils.sanitization import sanitize_search_query

# Validate and escape the focus_topic
safe_topic = sanitize_search_query(focus_topic)
if safe_topic:
    query = query.filter(
        Synthesis.synthesis_response.ilike(f"%{safe_topic}%")
    )
```

**File**: `backend/utils/sanitization.py` (add function)

```python
import re

def sanitize_search_query(query: str, max_length: int = 100) -> str:
    """
    Sanitize user input for use in SQL LIKE/ILIKE queries.

    - Escapes SQL wildcards (%, _)
    - Removes potentially dangerous characters
    - Limits length to prevent DoS
    - Returns empty string if input is invalid
    """
    if not query or not isinstance(query, str):
        return ""

    # Truncate to max length
    query = query[:max_length]

    # Escape SQL LIKE wildcards
    query = query.replace("%", "\\%")
    query = query.replace("_", "\\_")

    # Remove any remaining dangerous characters
    # Allow alphanumeric, spaces, common punctuation
    query = re.sub(r'[^\w\s\-\.,\'\"()]', '', query)

    return query.strip()
```

**Also check and fix in**:
- `backend/routes/search.py` - Any user input used in filters
- `backend/routes/themes.py` - Search functionality

---

### 46.2 Error Response Sanitization (M5)

**File**: `backend/app.py`

**Current Code** (exposes sensitive data):
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    error_detail = f"{type(exc).__name__}: {str(exc)}\n{traceback.format_exc()}"
    logger.error(f"Global exception handler: {error_detail}")

    return JSONResponse(
        status_code=500,
        content={
            "detail": error_detail,  # Full traceback exposed!
            "error_type": type(exc).__name__,
            "error_message": str(exc)
        }
    )
```

**Fixed Code**:
```python
from backend.utils.sanitization import redact_sensitive_data

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback

    # Full detail for logging (internal)
    full_traceback = traceback.format_exc()
    logger.error(f"Global exception handler: {type(exc).__name__}: {str(exc)}\n{full_traceback}")

    # Redacted detail for response (external)
    safe_message = redact_sensitive_data(str(exc))

    # In production, don't expose traceback
    is_production = os.getenv("RAILWAY_ENV") == "production"

    return JSONResponse(
        status_code=500,
        content={
            "detail": safe_message if is_production else f"{type(exc).__name__}: {safe_message}",
            "error_type": type(exc).__name__,
            "error_message": safe_message,
            # Only include traceback in development
            "traceback": None if is_production else redact_sensitive_data(full_traceback)
        }
    )
```

**File**: `backend/utils/sanitization.py` (add function)

```python
import re

# Patterns that might contain sensitive data
SENSITIVE_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey)["\']?\s*[:=]\s*["\']?[\w\-]+', '[REDACTED_API_KEY]'),
    (r'(?i)(password|passwd|pwd)["\']?\s*[:=]\s*["\']?[^\s"\']+', '[REDACTED_PASSWORD]'),
    (r'(?i)(secret|token)["\']?\s*[:=]\s*["\']?[\w\-]+', '[REDACTED_SECRET]'),
    (r'(?i)(auth|authorization)["\']?\s*[:=]\s*["\']?[^\s"\']+', '[REDACTED_AUTH]'),
    (r'sk-[a-zA-Z0-9]{20,}', '[REDACTED_ANTHROPIC_KEY]'),  # Anthropic API keys
    (r'Bearer\s+[\w\-\.]+', 'Bearer [REDACTED]'),  # Bearer tokens
    (r'Basic\s+[\w\+/=]+', 'Basic [REDACTED]'),  # Basic auth
]

def redact_sensitive_data(text: str) -> str:
    """
    Redact potentially sensitive data from error messages and tracebacks.

    Patterns redacted:
    - API keys (various formats)
    - Passwords
    - Tokens/secrets
    - Auth headers
    """
    if not text:
        return text

    result = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = re.sub(pattern, replacement, result)

    return result
```

---

### 46.3 Rate Limiting on Write Endpoints (H6)

**File**: `backend/routes/collect.py`

**Current Code** (no rate limiting on some endpoints):
```python
@router.post("/collect/discord")
async def collect_discord(...):
    # No rate limiting
```

**Fixed Code**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/collect/discord")
@limiter.limit("10/minute")  # Max 10 uploads per minute
async def collect_discord(request: Request, ...):
    ...

@router.post("/collect/42macro")
@limiter.limit("10/minute")
async def collect_42macro(request: Request, ...):
    ...

@router.post("/collect/youtube")
@limiter.limit("20/minute")  # Higher limit for batch uploads
async def collect_youtube(request: Request, ...):
    ...
```

**File**: `backend/routes/analyze.py`

```python
@router.post("/analyze/classify-batch")
@limiter.limit("5/minute")  # Analysis is expensive
async def classify_batch(request: Request, ...):
    ...
```

**File**: `backend/routes/synthesis.py`

```python
@router.post("/synthesis/generate")
@limiter.limit("3/minute")  # Synthesis is very expensive
async def generate_synthesis(request: Request, ...):
    ...
```

**Rate Limit Configuration**:

| Endpoint | Limit | Rationale |
|----------|-------|-----------|
| `POST /collect/discord` | 10/min | Reasonable batch uploads |
| `POST /collect/42macro` | 10/min | Reasonable batch uploads |
| `POST /collect/youtube` | 20/min | May have more items |
| `POST /collect/substack` | 10/min | RSS parsing |
| `POST /collect/kt-technical` | 10/min | Web scraping |
| `POST /analyze/classify-batch` | 5/min | CPU/API intensive |
| `POST /synthesis/generate` | 3/min | Very expensive (Opus) |
| `POST /themes/*/merge` | 5/min | Database writes |

---

## Definition of Done

### SQL Injection Prevention
- [ ] `sanitize_search_query()` function added to `backend/utils/sanitization.py`
- [ ] Function escapes SQL LIKE wildcards (%, _)
- [ ] Function removes dangerous characters
- [ ] Function enforces max length (100 chars)
- [ ] `synthesis.py` focus_topic parameter sanitized
- [ ] `search.py` search parameters sanitized
- [ ] `themes.py` search parameters sanitized
- [ ] All sanitization logged for audit

### Error Response Sanitization
- [ ] `redact_sensitive_data()` function added to `backend/utils/sanitization.py`
- [ ] Function redacts API keys, passwords, tokens, auth headers
- [ ] Function handles Anthropic key format (`sk-...`)
- [ ] Global exception handler uses redaction
- [ ] Full traceback only shown in development mode
- [ ] Production mode shows generic error message
- [ ] Sensitive data still logged server-side for debugging

### Rate Limiting
- [ ] Rate limits added to all `POST /collect/*` endpoints
- [ ] Rate limits added to `POST /analyze/classify-batch`
- [ ] Rate limits added to `POST /synthesis/generate`
- [ ] Rate limit exceeded returns 429 with retry-after header
- [ ] Rate limits configurable via environment variables (optional)

### Testing
- [ ] Unit tests pass (`tests/test_prd046_security.py`)
- [ ] Integration tests pass
- [ ] Manual penetration testing completed

### Documentation
- [ ] CLAUDE.md updated with security hardening info
- [ ] PRD moved to `/docs/archived/` on completion

---

## Testing Requirements

**Unit Tests** (`tests/test_prd046_security.py`):

```python
class TestSanitizeSearchQuery:
    def test_escapes_percent_wildcard(self):
        assert sanitize_search_query("100%") == "100\\%"

    def test_escapes_underscore_wildcard(self):
        assert sanitize_search_query("test_value") == "test\\_value"

    def test_removes_dangerous_chars(self):
        assert sanitize_search_query("'; DROP TABLE--") == " DROP TABLE"

    def test_enforces_max_length(self):
        long_input = "a" * 200
        assert len(sanitize_search_query(long_input)) == 100

    def test_handles_empty_input(self):
        assert sanitize_search_query("") == ""
        assert sanitize_search_query(None) == ""


class TestRedactSensitiveData:
    def test_redacts_api_key(self):
        text = 'api_key="sk-abc123"'
        assert "sk-abc123" not in redact_sensitive_data(text)

    def test_redacts_anthropic_key(self):
        text = "Error with key sk-ant-api03-xxxxxxxxxxxx"
        assert "sk-ant" not in redact_sensitive_data(text)

    def test_redacts_password(self):
        text = 'password: "secretpass123"'
        assert "secretpass123" not in redact_sensitive_data(text)

    def test_redacts_bearer_token(self):
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
        assert "eyJhbGciOiJIUzI1NiIs" not in redact_sensitive_data(text)

    def test_preserves_non_sensitive_data(self):
        text = "Connection failed to database"
        assert redact_sensitive_data(text) == text


class TestRateLimiting:
    def test_collect_discord_rate_limited(self):
        # Make 11 requests, 11th should be rate limited
        for i in range(10):
            response = client.post("/api/collect/discord", ...)
            assert response.status_code == 200
        response = client.post("/api/collect/discord", ...)
        assert response.status_code == 429

    def test_synthesis_generate_rate_limited(self):
        # Make 4 requests, 4th should be rate limited
        for i in range(3):
            response = client.post("/api/synthesis/generate", ...)
        response = client.post("/api/synthesis/generate", ...)
        assert response.status_code == 429
```

**Integration Tests**:
- Test SQL injection attempt returns no results (not error)
- Test error response doesn't contain API keys
- Test rate limiting persists across requests
- Test rate limit resets after window

**Manual Testing Checklist**:
- [ ] Try SQL injection in synthesis focus_topic
- [ ] Try SQL injection in search endpoint
- [ ] Trigger error with API key in message, verify not in response
- [ ] Verify rate limit 429 response includes Retry-After header
- [ ] Verify development mode shows traceback, production doesn't

---

## Dependencies

- PRD-037 (Security Hardening) - Existing sanitization infrastructure
- slowapi library (already in requirements.txt)

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Rate limits too aggressive | Start conservative; monitor and adjust |
| Redaction misses some patterns | Add patterns as discovered; log originals server-side |
| Performance impact of sanitization | Sanitization is O(n); negligible for typical inputs |
