# PRD-029: Layout & Navigation Restructure

## Overview

Redesign the overall page layout and navigation structure to improve information architecture, visual hierarchy, and user experience. Implement a modern dashboard layout with glassmorphic header, hero section, and improved content organization.

**Status**: Proposed
**Priority**: High
**Depends On**: PRD-027, PRD-028
**Blocks**: PRD-030, PRD-031

---

## Goals

1. Improve information hierarchy and content organization
2. Create a modern, professional dashboard layout
3. Implement sticky glassmorphic header with search
4. Add hero section for executive summary
5. Reorganize content into logical sections
6. Improve mobile navigation experience

---

## Current State Issues

| Issue | Impact |
|-------|--------|
| Redundant title (appears twice) | Confusing, wasted space |
| No global search | Hard to find specific content |
| Basic tab navigation | Limited information architecture |
| No hero/summary section | Key insights buried |
| Flat content structure | No visual hierarchy |
| Basic mobile hamburger | Poor mobile UX |

---

## New Layout Architecture

### Desktop Layout (>1024px)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ HEADER (Sticky, Glassmorphic)                                     h: 64px  │
│ ┌─────────┐ ┌──────────────────────────────┐ ┌─────┐ ┌─────┐ ┌───────────┐ │
│ │ Logo    │ │ ⌘K Search research...        │ │ 🔔  │ │ ⚙️  │ │ Live • 🟢 │ │
│ └─────────┘ └──────────────────────────────┘ └─────┘ └─────┘ └───────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ MAIN CONTENT AREA                                        max-width: 1400px │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ HERO SECTION - Executive Summary                              h: ~200px │ │
│ │ ┌───────────────────────────────────┐ ┌───────────────────────────────┐ │ │
│ │ │ Market Regime: TRANSITIONING      │ │ Key Insight                   │ │ │
│ │ │ [animated badge]                  │ │ "VIX structure suggests..."   │ │ │
│ │ │                                   │ │                               │ │ │
│ │ │ Last Updated: 7h ago              │ │ Primary Sources: Discord, YT  │ │ │
│ │ └───────────────────────────────────┘ └───────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐                    │
│ │ KPI Card  │ │ KPI Card  │ │ KPI Card  │ │ KPI Card  │     KPI ROW       │
│ │ Content   │ │ Active    │ │ Confluence│ │ Last      │                    │
│ │ (24h)     │ │ Themes    │ │ Score     │ │ Synthesis │                    │
│ └───────────┘ └───────────┘ └───────────┘ └───────────┘                    │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ TABS: [Overview] [Themes] [Sources] [History]              FILTER: 24h │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ TAB CONTENT AREA                                                            │
│ ┌─────────────────────────────────────┐ ┌─────────────────────────────────┐ │
│ │ MAIN COLUMN (60%)                   │ │ SIDEBAR (40%)                   │ │
│ │                                     │ │                                 │ │
│ │ Confluence Zones / Synthesis        │ │ Attention Priorities            │ │
│ │ Research narrative                  │ │ Source Status                   │ │
│ │ Theme details                       │ │ Quick Actions                   │ │
│ │                                     │ │                                 │ │
│ └─────────────────────────────────────┘ └─────────────────────────────────┘ │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ FLOATING ACTION BAR (Sticky bottom on scroll)                           │ │
│ │ [⚡ Analyze] [📝 Generate Synthesis] [🔄 Refresh] [⬇️ Export]           │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mobile Layout (<768px)

```
┌─────────────────────────────────┐
│ HEADER (Sticky)          h: 56px│
│ [≡] Logo            [🔔] [Live] │
├─────────────────────────────────┤
│ SEARCH BAR (Full width)         │
│ [🔍 Search research...]         │
├─────────────────────────────────┤
│ HERO (Condensed)                │
│ Regime: TRANSITIONING           │
│ "Key insight summary..."        │
├─────────────────────────────────┤
│ KPI CARDS (2x2 Grid)            │
│ ┌─────────┐ ┌─────────┐         │
│ │ Content │ │ Themes  │         │
│ └─────────┘ └─────────┘         │
│ ┌─────────┐ ┌─────────┐         │
│ │ Score   │ │ Updated │         │
│ └─────────┘ └─────────┘         │
├─────────────────────────────────┤
│ TABS (Horizontal scroll)        │
│ [Overview] [Themes] [Sources]..│
├─────────────────────────────────┤
│ CONTENT (Single column)         │
│                                 │
│                                 │
├─────────────────────────────────┤
│ BOTTOM ACTION BAR (Fixed)       │
│ [Analyze] [Generate] [More]     │
└─────────────────────────────────┘
```

---

## Implementation Tasks

### Task 1: New HTML Structure (`index.html`)

**File**: `frontend/index.html`

Update the HTML structure:

```html
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Macro Confluence Hub</title>

  <!-- Preconnect to Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

  <!-- Stylesheets -->
  <link rel="stylesheet" href="css/design-system.css">
  <link rel="stylesheet" href="css/components.css">
  <link rel="stylesheet" href="css/layout.css">
  <link rel="stylesheet" href="css/pages/dashboard.css">
</head>
<body>
  <!-- Skip to main content (accessibility) -->
  <a href="#main-content" class="skip-link">Skip to main content</a>

  <!-- Header -->
  <header class="header glass" id="site-header">
    <div class="header-container">
      <!-- Logo -->
      <a href="/" class="header-logo">
        <span class="logo-icon">📊</span>
        <span class="logo-text">Confluence<span class="logo-accent">Hub</span></span>
      </a>

      <!-- Search (Desktop) -->
      <div class="header-search desktop-only">
        <button class="search-trigger" id="search-trigger">
          <span class="search-icon">🔍</span>
          <span class="search-placeholder">Search research...</span>
          <kbd class="search-shortcut">⌘K</kbd>
        </button>
      </div>

      <!-- Header Actions -->
      <div class="header-actions">
        <!-- Notifications -->
        <button class="header-action-btn" id="notifications-btn" aria-label="Notifications">
          <span class="icon">🔔</span>
          <span class="notification-badge">3</span>
        </button>

        <!-- Settings -->
        <button class="header-action-btn" id="settings-btn" aria-label="Settings">
          <span class="icon">⚙️</span>
        </button>

        <!-- Connection Status -->
        <div class="connection-status" id="connection-status">
          <span class="live-dot"></span>
          <span class="status-text desktop-only">Live</span>
        </div>

        <!-- Mobile Menu Toggle -->
        <button class="mobile-menu-btn mobile-only" id="mobile-menu-btn" aria-label="Menu">
          <span class="hamburger-line"></span>
          <span class="hamburger-line"></span>
          <span class="hamburger-line"></span>
        </button>
      </div>
    </div>

    <!-- Mobile Search -->
    <div class="header-search-mobile mobile-only">
      <input type="search" class="search-input" placeholder="Search research...">
    </div>
  </header>

  <!-- Mobile Navigation Drawer -->
  <nav class="mobile-nav" id="mobile-nav" aria-hidden="true">
    <div class="mobile-nav-overlay"></div>
    <div class="mobile-nav-panel glass-strong">
      <div class="mobile-nav-header">
        <span class="logo-text">Confluence<span class="logo-accent">Hub</span></span>
        <button class="mobile-nav-close" id="mobile-nav-close">✕</button>
      </div>
      <ul class="mobile-nav-links">
        <li><a href="#overview" class="mobile-nav-link active">Overview</a></li>
        <li><a href="#themes" class="mobile-nav-link">Themes</a></li>
        <li><a href="#sources" class="mobile-nav-link">Sources</a></li>
        <li><a href="#history" class="mobile-nav-link">History</a></li>
      </ul>
      <div class="mobile-nav-actions">
        <button class="btn btn-primary w-full">Generate Synthesis</button>
      </div>
    </div>
  </nav>

  <!-- Main Content -->
  <main class="main-content" id="main-content">
    <div class="container">

      <!-- Hero Section -->
      <section class="hero-section" id="hero-section">
        <div class="hero-grid">
          <!-- Market Regime -->
          <div class="hero-regime card-glass">
            <div class="regime-label label">Market Regime</div>
            <div class="regime-badge regime-badge-transitioning" id="market-regime">
              <span class="regime-icon">⚡</span>
              <span class="regime-text">Transitioning</span>
            </div>
            <div class="regime-meta">
              <span class="text-muted">Last updated:</span>
              <span id="last-updated">7h ago</span>
            </div>
          </div>

          <!-- Key Insight -->
          <div class="hero-insight card-glass">
            <div class="insight-label label">Key Insight</div>
            <p class="insight-text" id="key-insight">
              VIX and volatility surface dynamics dominate, with options professionals
              tracking significant dealer positioning shifts around FOMC.
            </p>
            <div class="insight-sources">
              <span class="text-muted">Primary:</span>
              <span class="badge badge-discord">Discord</span>
              <span class="badge badge-youtube">YouTube</span>
            </div>
          </div>
        </div>
      </section>

      <!-- KPI Grid -->
      <section class="kpi-section" id="kpi-section">
        <div class="kpi-grid">
          <div class="kpi-card" id="kpi-content-24h">
            <div class="kpi-label">Content (24h)</div>
            <div class="kpi-value">
              <span class="data-large" id="content-24h-value">15</span>
              <span class="kpi-trend kpi-trend-up">+5</span>
            </div>
            <div class="kpi-sparkline" id="content-sparkline"></div>
            <div class="kpi-meta">items collected</div>
          </div>

          <div class="kpi-card" id="kpi-themes">
            <div class="kpi-label">Active Themes</div>
            <div class="kpi-value">
              <span class="data-large" id="themes-value">8</span>
              <span class="kpi-trend kpi-trend-neutral">—</span>
            </div>
            <div class="kpi-sparkline" id="themes-sparkline"></div>
            <div class="kpi-meta">across 5 sources</div>
          </div>

          <div class="kpi-card" id="kpi-confluence">
            <div class="kpi-label">Confluence Score</div>
            <div class="kpi-value">
              <span class="data-large" id="confluence-value">11</span>
              <span class="text-muted">/14</span>
            </div>
            <div class="confluence-meter">
              <div class="confluence-fill" style="width: 78%"></div>
            </div>
            <div class="kpi-meta">high agreement</div>
          </div>

          <div class="kpi-card" id="kpi-synthesis">
            <div class="kpi-label">Last Synthesis</div>
            <div class="kpi-value">
              <span class="data-large" id="synthesis-time">7h</span>
              <span class="text-muted">ago</span>
            </div>
            <div class="kpi-meta">24h window</div>
          </div>
        </div>
      </section>

      <!-- Tab Navigation -->
      <section class="tabs-section">
        <div class="tabs-header">
          <div class="tabs tabs-pills" role="tablist">
            <button class="tab active" role="tab" data-tab="overview" aria-selected="true">
              Overview
            </button>
            <button class="tab" role="tab" data-tab="themes" aria-selected="false">
              Themes
            </button>
            <button class="tab" role="tab" data-tab="sources" aria-selected="false">
              Sources
            </button>
            <button class="tab" role="tab" data-tab="history" aria-selected="false">
              History
            </button>
          </div>

          <div class="tabs-filter">
            <select class="select" id="time-filter">
              <option value="24h">Last 24 hours</option>
              <option value="7d" selected>Last 7 days</option>
              <option value="30d">Last 30 days</option>
            </select>
          </div>
        </div>
      </section>

      <!-- Tab Content -->
      <section class="tab-content">
        <!-- Overview Tab -->
        <div class="tab-panel active" id="panel-overview" role="tabpanel">
          <div class="content-grid">
            <!-- Main Column -->
            <div class="content-main">
              <!-- Synthesis Panel -->
              <div class="synthesis-panel card-glass card-accent" id="synthesis-panel">
                <div class="card-header">
                  <div>
                    <h2 class="card-title">Research Synthesis</h2>
                    <p class="card-subtitle">
                      <span id="synthesis-meta">24h analysis | 6 items | Dec 8, 2025</span>
                    </p>
                  </div>
                  <div id="synthesis-regime"></div>
                </div>

                <div class="card-body">
                  <div class="synthesis-content" id="synthesis-content">
                    <!-- Dynamic synthesis content -->
                  </div>

                  <div class="synthesis-themes" id="synthesis-themes">
                    <!-- Dynamic theme tags -->
                  </div>
                </div>
              </div>

              <!-- Confluence Zones -->
              <div class="confluence-section" id="confluence-section">
                <h3 class="section-title">Confluence Zones</h3>
                <div class="confluence-list" id="confluence-zones">
                  <!-- Dynamic confluence zones -->
                </div>
              </div>

              <!-- High Conviction Ideas -->
              <div class="ideas-section" id="ideas-section">
                <h3 class="section-title">High-Conviction Ideas</h3>
                <div class="ideas-list" id="conviction-ideas">
                  <!-- Dynamic ideas -->
                </div>
              </div>
            </div>

            <!-- Sidebar -->
            <aside class="content-sidebar">
              <!-- Attention Priorities -->
              <div class="sidebar-card card-glass">
                <h3 class="sidebar-title">Attention Priorities</h3>
                <div class="priority-list" id="attention-priorities">
                  <!-- Dynamic priorities -->
                </div>
              </div>

              <!-- Source Status -->
              <div class="sidebar-card card-glass">
                <h3 class="sidebar-title">Source Status</h3>
                <div class="source-list" id="source-status">
                  <!-- Dynamic source cards -->
                </div>
              </div>

              <!-- Quick Actions -->
              <div class="sidebar-card card-glass">
                <h3 class="sidebar-title">Quick Actions</h3>
                <div class="quick-actions">
                  <button class="btn btn-secondary btn-sm w-full mb-2" id="btn-collect-youtube">
                    Collect YouTube
                  </button>
                  <button class="btn btn-secondary btn-sm w-full mb-2" id="btn-collect-substack">
                    Collect Substack
                  </button>
                  <button class="btn btn-secondary btn-sm w-full" id="btn-collect-kt">
                    Collect KT Technical
                  </button>
                </div>
              </div>
            </aside>
          </div>
        </div>

        <!-- Themes Tab -->
        <div class="tab-panel" id="panel-themes" role="tabpanel">
          <!-- Themes content -->
        </div>

        <!-- Sources Tab -->
        <div class="tab-panel" id="panel-sources" role="tabpanel">
          <!-- Sources content -->
        </div>

        <!-- History Tab -->
        <div class="tab-panel" id="panel-history" role="tabpanel">
          <!-- History content -->
        </div>
      </section>

    </div>
  </main>

  <!-- Floating Action Bar -->
  <div class="floating-action-bar glass" id="floating-actions">
    <div class="fab-container">
      <button class="btn btn-warning" id="btn-analyze">
        <span class="icon">⚡</span>
        <span class="btn-text">Analyze</span>
      </button>
      <button class="btn btn-primary" id="btn-generate-24h">
        <span class="icon">📝</span>
        <span class="btn-text">Generate 24h</span>
      </button>
      <button class="btn btn-secondary" id="btn-generate-7d">
        <span class="icon">📊</span>
        <span class="btn-text">Generate 7-Day</span>
      </button>
      <button class="btn btn-ghost" id="btn-refresh">
        <span class="icon">🔄</span>
        <span class="btn-text desktop-only">Refresh</span>
      </button>
    </div>
  </div>

  <!-- Search Modal -->
  <div class="modal" id="search-modal" aria-hidden="true">
    <div class="modal-backdrop"></div>
    <div class="modal-content glass-strong search-modal-content">
      <div class="search-modal-header">
        <input type="search" class="search-modal-input" placeholder="Search themes, sources, content..." autofocus>
        <kbd class="search-modal-esc">ESC</kbd>
      </div>
      <div class="search-modal-results" id="search-results">
        <!-- Dynamic search results -->
      </div>
    </div>
  </div>

  <!-- Toast Container -->
  <div class="toast-container" id="toast-container"></div>

  <!-- Scripts -->
  <script src="js/components/ripple.js"></script>
  <script src="js/components/toast.js"></script>
  <script src="js/api.js"></script>
  <script src="js/utils.js"></script>
  <script src="js/websocket.js"></script>
  <script src="js/app.js"></script>
</body>
</html>
```

**Acceptance Criteria**:
- [ ] Semantic HTML5 structure
- [ ] Accessibility landmarks (header, main, nav)
- [ ] Skip link for keyboard navigation
- [ ] ARIA attributes on interactive elements
- [ ] Mobile-responsive structure
- [ ] Modular sections

---

### Task 2: Layout Styles (`layout.css`)

**File**: `frontend/css/layout.css`

```css
/**
 * Layout Styles
 * Page structure, header, navigation, content areas
 */

/* ============================================
   BASE LAYOUT
   ============================================ */
html {
  scroll-behavior: smooth;
}

body {
  background: var(--bg-base);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.container {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 var(--space-6);
}

.main-content {
  flex: 1;
  padding-top: calc(64px + var(--space-6)); /* Header height + spacing */
  padding-bottom: calc(80px + var(--space-6)); /* FAB height + spacing */
}

/* ============================================
   HEADER
   ============================================ */
.header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 64px;
  z-index: var(--z-sticky);
  transition: all var(--duration-200) var(--ease-in-out);
}

.header.scrolled {
  box-shadow: var(--shadow-dark-md);
}

.header-container {
  max-width: 1400px;
  margin: 0 auto;
  height: 100%;
  padding: 0 var(--space-6);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

/* Logo */
.header-logo {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  text-decoration: none;
  flex-shrink: 0;
}

.logo-icon {
  font-size: var(--text-xl);
}

.logo-text {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--text-primary);
}

.logo-accent {
  color: var(--interactive-default);
}

/* Search Trigger */
.header-search {
  flex: 1;
  max-width: 480px;
}

.search-trigger {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-4);
  background: var(--bg-glass);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-muted);
  cursor: pointer;
  transition: all var(--duration-200) var(--ease-in-out);
}

.search-trigger:hover {
  background: var(--bg-glass-hover);
  border-color: var(--border-medium);
}

.search-icon {
  font-size: var(--text-base);
}

.search-placeholder {
  flex: 1;
  text-align: left;
  font-size: var(--text-sm);
}

.search-shortcut {
  padding: var(--space-1) var(--space-2);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-family: var(--font-sans);
  color: var(--text-muted);
}

/* Header Actions */
.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.header-action-btn {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-lg);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-150) var(--ease-in-out);
}

.header-action-btn:hover {
  background: var(--bg-glass);
  color: var(--text-primary);
}

.header-action-btn .icon {
  font-size: var(--text-lg);
}

.notification-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 16px;
  height: 16px;
  padding: 0 var(--space-1);
  background: var(--status-danger);
  border-radius: var(--radius-full);
  font-size: 10px;
  font-weight: var(--font-bold);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Connection Status */
.connection-status {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--bg-glass);
  border-radius: var(--radius-full);
}

.status-text {
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
}

/* Mobile Menu Button */
.mobile-menu-btn {
  width: 40px;
  height: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  background: transparent;
  border: none;
  cursor: pointer;
}

.hamburger-line {
  width: 20px;
  height: 2px;
  background: var(--text-primary);
  border-radius: 1px;
  transition: all var(--duration-200) var(--ease-in-out);
}

.mobile-menu-btn.active .hamburger-line:nth-child(1) {
  transform: rotate(45deg) translate(4px, 4px);
}

.mobile-menu-btn.active .hamburger-line:nth-child(2) {
  opacity: 0;
}

.mobile-menu-btn.active .hamburger-line:nth-child(3) {
  transform: rotate(-45deg) translate(4px, -4px);
}

/* Header Mobile Search */
.header-search-mobile {
  padding: var(--space-2) var(--space-4);
  border-top: 1px solid var(--border-subtle);
}

/* ============================================
   MOBILE NAVIGATION
   ============================================ */
.mobile-nav {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal);
  pointer-events: none;
  opacity: 0;
  transition: opacity var(--duration-200) var(--ease-in-out);
}

.mobile-nav.active {
  pointer-events: auto;
  opacity: 1;
}

.mobile-nav-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
}

.mobile-nav-panel {
  position: absolute;
  top: 0;
  right: 0;
  width: 280px;
  height: 100%;
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  transform: translateX(100%);
  transition: transform var(--duration-300) var(--ease-out);
}

.mobile-nav.active .mobile-nav-panel {
  transform: translateX(0);
}

.mobile-nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-8);
}

.mobile-nav-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-glass);
  border: none;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
}

.mobile-nav-links {
  list-style: none;
  margin: 0;
  padding: 0;
  flex: 1;
}

.mobile-nav-link {
  display: block;
  padding: var(--space-4);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: var(--text-lg);
  font-weight: var(--font-medium);
  border-radius: var(--radius-lg);
  transition: all var(--duration-150) var(--ease-in-out);
}

.mobile-nav-link:hover,
.mobile-nav-link.active {
  background: var(--bg-glass);
  color: var(--text-primary);
}

.mobile-nav-actions {
  padding-top: var(--space-6);
  border-top: 1px solid var(--border-subtle);
}

/* ============================================
   HERO SECTION
   ============================================ */
.hero-section {
  margin-bottom: var(--space-6);
}

.hero-grid {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: var(--space-4);
}

.hero-regime,
.hero-insight {
  padding: var(--space-5);
}

.regime-label,
.insight-label {
  margin-bottom: var(--space-3);
}

.regime-meta {
  margin-top: var(--space-4);
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.insight-text {
  font-size: var(--text-lg);
  line-height: var(--leading-relaxed);
  color: var(--text-primary);
  margin-bottom: var(--space-4);
}

.insight-sources {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
}

/* ============================================
   KPI SECTION
   ============================================ */
.kpi-section {
  margin-bottom: var(--space-6);
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
}

/* ============================================
   TABS SECTION
   ============================================ */
.tabs-section {
  margin-bottom: var(--space-6);
}

.tabs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.tabs-filter {
  flex-shrink: 0;
}

.tabs-filter .select {
  min-width: 160px;
}

/* ============================================
   CONTENT GRID
   ============================================ */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: var(--space-6);
  align-items: start;
}

.content-main {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.content-sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  position: sticky;
  top: calc(64px + var(--space-6));
}

/* Section Titles */
.section-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin-bottom: var(--space-4);
}

/* Sidebar Cards */
.sidebar-card {
  padding: var(--space-5);
}

.sidebar-title {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin-bottom: var(--space-4);
}

/* ============================================
   FLOATING ACTION BAR
   ============================================ */
.floating-action-bar {
  position: fixed;
  bottom: var(--space-6);
  left: 50%;
  transform: translateX(-50%);
  z-index: var(--z-sticky);
  border-radius: var(--radius-2xl);
  padding: var(--space-3);
  transition: all var(--duration-200) var(--ease-in-out);
}

.floating-action-bar.hidden {
  transform: translateX(-50%) translateY(100px);
  opacity: 0;
  pointer-events: none;
}

.fab-container {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.fab-container .btn {
  white-space: nowrap;
}

.fab-container .btn .icon {
  font-size: var(--text-base);
}

/* ============================================
   SEARCH MODAL
   ============================================ */
.search-modal-content {
  position: absolute;
  top: 20%;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 640px;
  border-radius: var(--radius-2xl);
  overflow: hidden;
}

.search-modal-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border-bottom: 1px solid var(--border-subtle);
}

.search-modal-input {
  flex: 1;
  background: transparent;
  border: none;
  font-size: var(--text-lg);
  color: var(--text-primary);
  outline: none;
}

.search-modal-input::placeholder {
  color: var(--text-muted);
}

.search-modal-esc {
  padding: var(--space-1) var(--space-2);
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  color: var(--text-muted);
}

.search-modal-results {
  max-height: 400px;
  overflow-y: auto;
  padding: var(--space-4);
}

/* ============================================
   RESPONSIVE LAYOUT
   ============================================ */

/* Tablet */
@media (max-width: 1024px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }

  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .content-grid {
    grid-template-columns: 1fr;
  }

  .content-sidebar {
    position: static;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-4);
  }

  .content-sidebar .sidebar-card:last-child {
    grid-column: span 2;
  }
}

/* Mobile */
@media (max-width: 768px) {
  .container {
    padding: 0 var(--space-4);
  }

  .main-content {
    padding-top: calc(56px + var(--space-4));
    padding-bottom: calc(72px + var(--space-4));
  }

  .header {
    height: 56px;
  }

  .header-container {
    padding: 0 var(--space-4);
  }

  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-3);
  }

  .content-sidebar {
    grid-template-columns: 1fr;
  }

  .content-sidebar .sidebar-card:last-child {
    grid-column: span 1;
  }

  .tabs-header {
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-3);
  }

  .tabs {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
  }

  .tabs::-webkit-scrollbar {
    display: none;
  }

  .floating-action-bar {
    left: var(--space-4);
    right: var(--space-4);
    transform: none;
    bottom: var(--space-4);
  }

  .fab-container {
    justify-content: center;
  }

  .fab-container .btn-text {
    display: none;
  }

  .fab-container .btn {
    padding: var(--space-3);
  }
}

/* ============================================
   UTILITY CLASSES
   ============================================ */
.desktop-only {
  display: block;
}

.mobile-only {
  display: none;
}

@media (max-width: 768px) {
  .desktop-only {
    display: none;
  }

  .mobile-only {
    display: block;
  }
}

.w-full {
  width: 100%;
}
```

**Acceptance Criteria**:
- [ ] Sticky glassmorphic header
- [ ] Search trigger with keyboard shortcut
- [ ] Mobile navigation drawer
- [ ] Hero section layout
- [ ] KPI grid
- [ ] Two-column content layout
- [ ] Sticky sidebar
- [ ] Floating action bar
- [ ] Search modal
- [ ] Responsive breakpoints (tablet, mobile)

---

### Task 3: Navigation JavaScript

**File**: `frontend/js/navigation.js`

```javascript
/**
 * Navigation & Layout JavaScript
 * Handles mobile menu, search modal, tabs, scroll behavior
 */

// ============================================
// MOBILE NAVIGATION
// ============================================
const mobileNav = {
  nav: document.getElementById('mobile-nav'),
  menuBtn: document.getElementById('mobile-menu-btn'),
  closeBtn: document.getElementById('mobile-nav-close'),
  overlay: document.querySelector('.mobile-nav-overlay'),

  init() {
    if (!this.nav || !this.menuBtn) return;

    this.menuBtn.addEventListener('click', () => this.toggle());
    this.closeBtn?.addEventListener('click', () => this.close());
    this.overlay?.addEventListener('click', () => this.close());

    // Close on escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.nav.classList.contains('active')) {
        this.close();
      }
    });

    // Close on link click
    this.nav.querySelectorAll('.mobile-nav-link').forEach(link => {
      link.addEventListener('click', () => this.close());
    });
  },

  toggle() {
    this.nav.classList.toggle('active');
    this.menuBtn.classList.toggle('active');
    document.body.style.overflow = this.nav.classList.contains('active') ? 'hidden' : '';
  },

  close() {
    this.nav.classList.remove('active');
    this.menuBtn.classList.remove('active');
    document.body.style.overflow = '';
  }
};

// ============================================
// SEARCH MODAL
// ============================================
const searchModal = {
  modal: document.getElementById('search-modal'),
  trigger: document.getElementById('search-trigger'),
  input: null,

  init() {
    if (!this.modal) return;

    this.input = this.modal.querySelector('.search-modal-input');
    const backdrop = this.modal.querySelector('.modal-backdrop');

    // Open on trigger click
    this.trigger?.addEventListener('click', () => this.open());

    // Open on Cmd/Ctrl + K
    document.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        this.open();
      }
    });

    // Close on escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !this.modal.getAttribute('aria-hidden')) {
        this.close();
      }
    });

    // Close on backdrop click
    backdrop?.addEventListener('click', () => this.close());
  },

  open() {
    this.modal.setAttribute('aria-hidden', 'false');
    this.modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    this.input?.focus();
  },

  close() {
    this.modal.setAttribute('aria-hidden', 'true');
    this.modal.classList.remove('active');
    document.body.style.overflow = '';
    if (this.input) this.input.value = '';
  }
};

// ============================================
// TAB NAVIGATION
// ============================================
const tabs = {
  init() {
    const tabButtons = document.querySelectorAll('[role="tab"]');
    const tabPanels = document.querySelectorAll('[role="tabpanel"]');

    tabButtons.forEach(button => {
      button.addEventListener('click', () => {
        const tabId = button.dataset.tab;

        // Update button states
        tabButtons.forEach(btn => {
          btn.classList.remove('active');
          btn.setAttribute('aria-selected', 'false');
        });
        button.classList.add('active');
        button.setAttribute('aria-selected', 'true');

        // Update panel visibility
        tabPanels.forEach(panel => {
          panel.classList.remove('active');
        });
        const targetPanel = document.getElementById(`panel-${tabId}`);
        targetPanel?.classList.add('active');

        // Update URL hash without scrolling
        history.replaceState(null, '', `#${tabId}`);
      });
    });

    // Handle initial hash
    const hash = window.location.hash.slice(1);
    if (hash) {
      const targetTab = document.querySelector(`[data-tab="${hash}"]`);
      targetTab?.click();
    }
  }
};

// ============================================
// HEADER SCROLL BEHAVIOR
// ============================================
const headerScroll = {
  header: document.getElementById('site-header'),
  fab: document.getElementById('floating-actions'),
  lastScroll: 0,

  init() {
    if (!this.header) return;

    window.addEventListener('scroll', () => this.handleScroll(), { passive: true });
  },

  handleScroll() {
    const currentScroll = window.scrollY;

    // Add shadow on scroll
    if (currentScroll > 10) {
      this.header.classList.add('scrolled');
    } else {
      this.header.classList.remove('scrolled');
    }

    // Hide FAB on scroll down, show on scroll up
    if (this.fab) {
      if (currentScroll > this.lastScroll && currentScroll > 200) {
        this.fab.classList.add('hidden');
      } else {
        this.fab.classList.remove('hidden');
      }
    }

    this.lastScroll = currentScroll;
  }
};

// ============================================
// SMOOTH SCROLL FOR ANCHOR LINKS
// ============================================
const smoothScroll = {
  init() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', (e) => {
        const target = document.querySelector(anchor.getAttribute('href'));
        if (target) {
          e.preventDefault();
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      });
    });
  }
};

// ============================================
// INITIALIZE ALL
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  mobileNav.init();
  searchModal.init();
  tabs.init();
  headerScroll.init();
  smoothScroll.init();
});

// Export for external use
window.navigation = {
  mobileNav,
  searchModal,
  tabs
};
```

**Acceptance Criteria**:
- [ ] Mobile navigation toggle
- [ ] Search modal with ⌘K shortcut
- [ ] Tab navigation with URL hash
- [ ] Header scroll effects
- [ ] Smooth scroll for anchors
- [ ] Keyboard accessibility

---

### Task 4: Modal Component CSS & JS

**File**: `frontend/css/components/_modals.css`

```css
/**
 * Modal Components
 */

.modal {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: var(--space-6);
  opacity: 0;
  visibility: hidden;
  transition: all var(--duration-200) var(--ease-in-out);
}

.modal.active,
.modal[aria-hidden="false"] {
  opacity: 1;
  visibility: visible;
}

.modal-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
}

.modal-content {
  position: relative;
  width: 100%;
  max-width: 500px;
  max-height: calc(100vh - var(--space-12));
  overflow: auto;
  border-radius: var(--radius-2xl);
  transform: scale(0.95) translateY(-20px);
  transition: transform var(--duration-200) var(--ease-out);
}

.modal.active .modal-content,
.modal[aria-hidden="false"] .modal-content {
  transform: scale(1) translateY(0);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5);
  border-bottom: 1px solid var(--border-subtle);
}

.modal-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--text-muted);
  cursor: pointer;
  transition: all var(--duration-150) var(--ease-in-out);
}

.modal-close:hover {
  background: var(--bg-glass);
  color: var(--text-primary);
}

.modal-body {
  padding: var(--space-5);
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-5);
  border-top: 1px solid var(--border-subtle);
}

/* Size variants */
.modal-sm .modal-content {
  max-width: 400px;
}

.modal-lg .modal-content {
  max-width: 700px;
}

.modal-xl .modal-content {
  max-width: 900px;
}

.modal-fullscreen .modal-content {
  max-width: none;
  width: calc(100% - var(--space-8));
  height: calc(100% - var(--space-8));
  max-height: none;
  border-radius: var(--radius-xl);
}
```

---

### Task 5: Responsive Testing Checklist

Create automated responsive testing:

**File**: `frontend/js/responsive-test.js` (Development only)

```javascript
/**
 * Responsive Testing Utility
 * For development debugging
 */

const responsiveTest = {
  breakpoints: {
    mobile: 375,
    tablet: 768,
    desktop: 1024,
    wide: 1280
  },

  showCurrentBreakpoint() {
    const width = window.innerWidth;
    let current = 'wide';

    if (width < this.breakpoints.tablet) current = 'mobile';
    else if (width < this.breakpoints.desktop) current = 'tablet';
    else if (width < this.breakpoints.wide) current = 'desktop';

    console.log(`Current breakpoint: ${current} (${width}px)`);
  },

  init() {
    // Only in development
    if (window.location.hostname !== 'localhost') return;

    // Show breakpoint on resize
    window.addEventListener('resize', () => this.showCurrentBreakpoint());

    // Initial log
    this.showCurrentBreakpoint();

    // Add debug indicator
    const indicator = document.createElement('div');
    indicator.id = 'responsive-indicator';
    indicator.style.cssText = `
      position: fixed;
      bottom: 10px;
      left: 10px;
      padding: 4px 8px;
      background: rgba(0,0,0,0.8);
      color: white;
      font-size: 12px;
      font-family: monospace;
      border-radius: 4px;
      z-index: 9999;
    `;
    document.body.appendChild(indicator);

    const updateIndicator = () => {
      const width = window.innerWidth;
      let bp = 'wide';
      if (width < this.breakpoints.tablet) bp = 'mobile';
      else if (width < this.breakpoints.desktop) bp = 'tablet';
      else if (width < this.breakpoints.wide) bp = 'desktop';
      indicator.textContent = `${bp}: ${width}px`;
    };

    window.addEventListener('resize', updateIndicator);
    updateIndicator();
  }
};

// Auto-init in development
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => responsiveTest.init());
} else {
  responsiveTest.init();
}
```

---

## Testing Checklist

### Desktop (>1024px)
- [ ] Header displays correctly with search
- [ ] Hero section shows regime and insight
- [ ] KPI grid shows 4 columns
- [ ] Content grid shows main + sidebar
- [ ] Sidebar is sticky on scroll
- [ ] FAB shows all button labels

### Tablet (768-1024px)
- [ ] Header adapts correctly
- [ ] Hero stacks to single column
- [ ] KPI grid shows 2 columns
- [ ] Content becomes single column
- [ ] Sidebar becomes 2-column grid

### Mobile (<768px)
- [ ] Mobile menu works
- [ ] Search is accessible
- [ ] KPI shows 2x2 grid
- [ ] Everything single column
- [ ] FAB shows icons only
- [ ] Touch targets are 44px+

### Accessibility
- [ ] Skip link works
- [ ] Keyboard navigation functional
- [ ] Focus states visible
- [ ] Screen reader compatible
- [ ] ARIA attributes correct

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Layout Shift (CLS) | < 0.1 |
| Mobile Usability Score | 100 |
| Navigation Time | < 2 clicks |
| Header Height | 64px desktop, 56px mobile |

---

*Created: December 2025*
*Author: Claude Code Assistant*
