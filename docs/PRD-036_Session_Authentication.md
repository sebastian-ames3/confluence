# PRD-036: Session Authentication (JWT)

**Status**: Complete
**Priority**: High
**Estimated Complexity**: Medium-High
**Completed**: 2025-12-12

## Overview

Replaced browser-native HTTP Basic Auth dialogs with JWT-based session authentication, providing a login modal, persistent sessions (24-hour expiration), auto-refresh, and full backward compatibility for local collection scripts.

## Goals

1. Eliminate browser password dialogs with a proper login UI
2. JWT tokens for persistent session management (24-hour expiration)
3. Seamless token refresh before expiration
4. Backward compatibility: HTTP Basic Auth still works for local scripts
5. Logout functionality

## Implementation Summary

### 36.1 Dependencies

**File modified**: `requirements.txt`

Added PyJWT for JWT token handling:
```
PyJWT>=2.8.0,<3.0.0
```

### 36.2 JWT Utilities

**File modified**: `backend/utils/auth.py`

Added JWT constants and utility functions:
- `JWT_SECRET` - Falls back to AUTH_PASSWORD if not set
- `JWT_ALGORITHM` - HS256
- `JWT_EXPIRATION_HOURS` - 24 hours
- `JWT_REFRESH_THRESHOLD_MINUTES` - 60 minutes

New functions:
- `create_access_token(username)` - Generate JWT with expiration
- `decode_token(token)` - Validate and decode JWT
- `get_token_expiration(token)` - Get expiration time
- `should_refresh_token(token)` - Check if close to expiration
- `verify_jwt_or_basic()` - New dependency accepting Bearer OR Basic Auth

### 36.3 Auth Router

**New file**: `backend/routes/auth.py`

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/auth/login` | POST | None | Return JWT for valid credentials |
| `/api/auth/logout` | POST | JWT | Confirm logout (client-side) |
| `/api/auth/refresh` | POST | JWT | Return new token |
| `/api/auth/me` | GET | JWT | Return username + token status |

### 36.4 App Router Registration

**File modified**: `backend/app.py`

Added auth router at `/api/auth` prefix.

### 36.5 Route Migration

**Files modified** (replaced `verify_credentials` with `verify_jwt_or_basic`):
- `backend/routes/dashboard.py`
- `backend/routes/synthesis.py`
- `backend/routes/confluence.py`
- `backend/routes/search.py`

**Unchanged** (remain unauthenticated for local scripts):
- `backend/routes/collect.py`
- `backend/routes/analyze.py`
- `backend/routes/themes.py`
- `backend/routes/heartbeat.py`

### 36.6 Frontend Auth Manager

**New file**: `frontend/js/auth.js`

AuthManager provides:
- Token storage in localStorage
- `login(username, password)` - Authenticate and store token
- `logout()` - Clear token and show login modal
- `refreshToken()` - Get new token before expiration
- `scheduleRefresh()` - Auto-refresh timer
- `showLoginModal()` / `hideLoginModal()` - UI control
- `handleAuthError()` - Handle 401 responses
- `updateUI()` - Show/hide user menu

### 36.7 API Integration

**File modified**: `frontend/js/api.js`

- Added Bearer token header to all `apiFetch()` requests
- Added 401 response handling to trigger login modal

### 36.8 Login UI

**File modified**: `frontend/index.html`

Added:
- Login modal with username/password form
- User menu in header with username and logout button
- Script includes for api.js and auth.js

### 36.9 CSS Styles

**File modified**: `frontend/css/components/_modals.css`

Added styles for:
- `.login-modal-content` - Modal layout
- `.login-modal-header` - Header with logo and title
- `.login-form` - Form styling
- `.login-error` - Error message display
- `.modal.active` state selectors
- `.user-menu` - Header user menu
- `.logout-btn` - Logout button styling

## New Environment Variable

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `JWT_SECRET` | No | AUTH_PASSWORD | JWT signing key |

## API Changes

### New Endpoints

#### POST /api/auth/login

Request:
```json
{
  "username": "string",
  "password": "string"
}
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_at": "2025-12-13T12:00:00Z",
  "username": "sames3"
}
```

#### POST /api/auth/logout

Requires Bearer token. Returns:
```json
{
  "message": "Successfully logged out",
  "success": true
}
```

#### POST /api/auth/refresh

Requires Bearer token. Returns:
```json
{
  "access_token": "eyJ...",
  "expires_at": "2025-12-13T12:00:00Z",
  "username": "sames3"
}
```

#### GET /api/auth/me

Requires Bearer token. Returns:
```json
{
  "username": "sames3",
  "expires_at": "2025-12-13T12:00:00Z",
  "should_refresh": false
}
```

## Testing

**Test file**: `tests/test_prd036_auth.py`

32 unit tests covering:
- Dependencies (PyJWT installation)
- JWT utilities (create, decode, validate, expiration)
- Auth endpoints (login, logout, refresh, me)
- Route migration (verify_jwt_or_basic usage)
- Backward compatibility (Basic Auth still works)
- Frontend integration (auth.js, api.js, index.html, CSS)

## Definition of Done

- [x] PyJWT added to requirements.txt
- [x] JWT utilities working (create, decode, validate)
- [x] `verify_jwt_or_basic` accepts both auth methods
- [x] Login endpoint returns valid JWT
- [x] Logout/refresh/me endpoints working
- [x] Protected routes migrated to new dependency
- [x] Frontend AuthManager handles login/logout/refresh
- [x] apiFetch includes Bearer token
- [x] Login modal appears on 401
- [x] User menu shows in header when logged in
- [x] Basic Auth still works (backward compat)
- [x] 32 unit tests created
- [x] Documentation complete

## Notes

### Backward Compatibility

- HTTP Basic Auth continues to work for all endpoints
- Local scripts (`discord_local.py`, `macro42_local.py`) need no changes
- Existing curl commands with `-u` flag continue to work

### Security Considerations

1. **JWT Secret**: Uses `JWT_SECRET` env var, falls back to `AUTH_PASSWORD`
2. **Token Storage**: localStorage (acceptable for single-user personal app)
3. **XSS Protection**: Existing sanitization from PRD-037
4. **HTTPS**: Railway deployment is HTTPS-only
5. **No Token Blacklist**: Logout is client-side only (stateless)
