# PRD-034: Observability Foundation

**Status**: Complete
**Priority**: Critical
**Estimated Complexity**: Medium
**Completed**: December 2025

## Overview

Add centralized error monitoring, environment validation, agent retry logic, and collector dry-run mode to improve system reliability and debugging capabilities.

## Goals

1. Immediate visibility into production errors via Sentry
2. Fail-fast on missing critical environment variables
3. Automatic retry with exponential backoff for Claude API calls
4. Safe testing of collectors without database writes

## Implementation Summary

### 34.1 Sentry Error Monitoring

**Files modified:**
- `backend/app.py` - Sentry SDK initialization
- `requirements.txt` - Added `sentry-sdk[fastapi]==2.19.0`

**Features:**
- Initializes Sentry only when `SENTRY_DSN` is configured
- 10% trace sampling for performance monitoring
- Tags errors with `RAILWAY_ENV` environment
- Sends no PII data

### 34.2 Environment Variable Validation

**Files modified:**
- `backend/app.py` - Added `validate_environment()` function

**Features:**
- Required vars: `CLAUDE_API_KEY`, `AUTH_USERNAME`, `AUTH_PASSWORD`
- Raises `RuntimeError` in production if missing
- Logs warning in development mode

### 34.3 Agent Retry Logic with Exponential Backoff

**Files modified:**
- `agents/base_agent.py` - Updated `call_claude()` method

**Features:**
- Default 3 retries with exponential backoff (1s, 2s, 4s)
- Maximum delay capped at 30 seconds
- Configurable `max_retries` parameter
- Logs retries at WARNING level, failures at ERROR level

### 34.4 Collector Dry-Run Mode

**Files modified:**
- `collectors/base_collector.py` - Added `dry_run` parameter
- `backend/routes/trigger.py` - Added `dry_run` support to `/api/trigger/collect`

**Features:**
- `dry_run` parameter in `BaseCollector.__init__()`
- Skips database writes, logs what would be saved
- Returns `dry_run: true` in response
- Logs sample items for verification

## New Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `SENTRY_DSN` | No | Sentry error monitoring DSN |

## API Changes

### POST /api/trigger/collect

New request parameter:
```json
{
  "sources": ["youtube", "substack"],
  "run_type": "manual",
  "dry_run": true
}
```

Response includes `dry_run` flag:
```json
{
  "status": "dry_run_completed",
  "job_id": null,
  "dry_run": true
}
```

## Definition of Done

- [x] **34.1 Sentry Integration**
  - [x] `sentry-sdk[fastapi]` added to requirements.txt
  - [x] Sentry initializes only when `SENTRY_DSN` is set
  - [x] Errors tagged with correct environment

- [x] **34.2 Environment Validation**
  - [x] App fails to start in production with missing required vars
  - [x] App starts in development with missing vars (warning logged)
  - [x] Error message clearly lists which variables are missing

- [x] **34.3 Agent Retry Logic**
  - [x] `call_claude()` retries up to 3 times by default
  - [x] Exponential backoff delays: 1s, 2s, 4s (capped at 30s)
  - [x] Retry attempts logged at WARNING level
  - [x] Final failure logged at ERROR level

- [x] **34.4 Dry-Run Mode**
  - [x] `BaseCollector` accepts `dry_run` parameter
  - [x] Dry-run mode logs items without database writes
  - [x] `/api/trigger/collect` supports `dry_run` parameter
  - [x] Response indicates `dry_run: true`
