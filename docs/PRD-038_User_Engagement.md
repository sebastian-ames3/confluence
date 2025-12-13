# PRD-038: User Engagement

**Status**: Complete
**Priority**: Medium
**Estimated Complexity**: Medium
**Completed**: December 2025

## Overview

Add user feedback mechanisms to the Confluence dashboard for synthesis and themes. Users can provide quick thumbs up/down feedback or detailed ratings via a modal.

## Goals

1. Enable simple feedback (thumbs up/down) on synthesis and themes
2. Enable detailed feedback via modal (star ratings + comments)
3. Show toast notifications for feedback confirmation
4. Integrate with existing accessibility infrastructure

## Implementation Summary

### 38.1 Database Models

**Files modified:**
- `backend/models.py`

**Models added:**
- `SynthesisFeedback` - User feedback on synthesis
  - `id`, `synthesis_id`, `is_helpful` (boolean), `accuracy_rating` (1-5), `usefulness_rating` (1-5), `comment`, `user`, `created_at`, `updated_at`
  - Foreign key to `syntheses.id` with CASCADE delete
  - Check constraints for rating ranges
  - Index on `(synthesis_id, user)` for fast lookups

- `ThemeFeedback` - User feedback on themes
  - `id`, `theme_id`, `is_relevant` (boolean), `quality_rating` (1-5), `comment`, `user`, `created_at`, `updated_at`
  - Foreign key to `themes.id` with CASCADE delete
  - Check constraints for rating ranges
  - Index on `(theme_id, user)` for fast lookups

### 38.2 Engagement API Routes

**Files created:**
- `backend/routes/engagement.py`

**Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/engagement/synthesis/{id}/simple` | POST | Submit thumbs up/down |
| `/api/engagement/synthesis/{id}/detailed` | POST | Submit star ratings + comment |
| `/api/engagement/synthesis/{id}/my-feedback` | GET | Get user's existing feedback |
| `/api/engagement/theme/{id}/simple` | POST | Submit thumbs up/down |
| `/api/engagement/theme/{id}/detailed` | POST | Submit quality rating + comment |
| `/api/engagement/theme/{id}/my-feedback` | GET | Get user's existing feedback |

**Features:**
- Async patterns using `get_async_db` and `AsyncSession` (PRD-035)
- JWT or Basic Auth via `verify_jwt_or_basic` dependency
- Rate limiting via slowapi
- Comment sanitization via `sanitize_content_text` (PRD-037)
- Upsert pattern: updates existing feedback if user already submitted

**Files modified:**
- `backend/app.py` - Registered engagement router

### 38.3 Frontend FeedbackManager

**Files created:**
- `frontend/js/feedback.js`

**FeedbackManager Object:**
- `init()` - Setup event delegation and modal events
- `setupEventDelegation()` - Handle dynamically added buttons
- `setupModalEvents()` - Close modal on backdrop click
- `submitSimpleFeedback(type, id, isPositive)` - Send thumbs up/down to API
- `openFeedbackModal(type, id)` - Open detailed feedback modal
- `loadExistingFeedback(type, id)` - Pre-populate form if editing
- `submitDetailedFeedback(e)` - Submit star ratings + comment
- `closeFeedbackModal()` - Close modal
- `updateFeedbackButtonStates(type, id, isPositive)` - Toggle active states
- `renderSynthesisFeedbackButtons(synthesisId)` - Generate synthesis buttons HTML
- `renderThemeFeedbackButtons(themeId)` - Generate theme buttons HTML

**Features:**
- Event delegation for dynamically added buttons
- Feedback state caching
- ToastManager integration for success/error notifications
- AccessibilityManager integration for screen reader announcements
- Exported to `window.FeedbackManager`

### 38.4 Feedback CSS

**Files modified:**
- `frontend/css/components/_buttons.css`

**Styles added:**
- `.feedback-buttons` - Container flex layout
- `.feedback-btn` - Icon button styling with hover effects
- `.feedback-btn.active` - Selected state
- `.feedback-btn[data-feedback-up].active` - Green for thumbs up
- `.feedback-btn[data-feedback-down].active` - Red for thumbs down
- `.feedback-btn-detailed` - "More feedback" link styling
- `.star-rating` - 5-star rating with row-reverse trick
- `.star-rating input:checked ~ label` - Highlight selected stars
- Focus visible styles for accessibility

### 38.5 UI Integration

**Files modified:**
- `frontend/index.html`

**Changes:**
- Added feedback modal HTML (after login modal)
  - Star ratings for accuracy/usefulness (synthesis) or quality (theme)
  - Textarea for optional comment (max 2000 chars)
  - Submit/Cancel buttons
- Added `<script src="js/feedback.js">` tag
- Added `#synthesis-feedback-buttons` container in takeaways section
- Added `currentSynthesisId` variable for tracking
- Modified `displaySynthesis()` to render feedback buttons
- Modified `displayThemes()` to include feedback buttons in theme cards

## Design Decisions

1. **Upsert pattern**: One feedback per user per synthesis/theme - resubmission updates existing
2. **Toast-only notifications**: No persistent notification storage - leverages existing ToastManager
3. **Async routes**: Follows PRD-035 patterns with `get_async_db`
4. **Input sanitization**: Uses `sanitize_content_text` for comments (PRD-037)
5. **Accessibility**: `aria-pressed` on toggle buttons, screen reader announcements

## Definition of Done

- [x] **38.1 Database Models**
  - [x] `SynthesisFeedback` model in models.py
  - [x] `ThemeFeedback` model in models.py
  - [x] Check constraints for ratings
  - [x] Indexes for user lookups

- [x] **38.2 Engagement Routes**
  - [x] `engagement.py` created with 6 endpoints
  - [x] Async patterns (get_async_db, AsyncSession)
  - [x] JWT/Basic Auth protection
  - [x] Rate limiting
  - [x] Comment sanitization
  - [x] Router registered in app.py

- [x] **38.3 Frontend**
  - [x] `feedback.js` created with FeedbackManager
  - [x] Event delegation for dynamic buttons
  - [x] Toast notifications on submit
  - [x] Accessibility announcements

- [x] **38.4 CSS**
  - [x] Feedback button styles
  - [x] Star rating styles
  - [x] Active/hover states
  - [x] Focus visible styles

- [x] **38.5 UI Integration**
  - [x] Feedback modal in index.html
  - [x] Script tag added
  - [x] Feedback buttons in displaySynthesis()
  - [x] Feedback buttons in displayThemes()

- [x] **Tests**
  - [x] 45+ unit tests in `tests/test_prd038_engagement.py`
  - [x] All existing tests pass
