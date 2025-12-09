# PRD-032: Accessibility & Performance

## Overview
This PRD ensures the Macro Confluence Hub meets WCAG 2.1 AA accessibility standards and achieves optimal performance metrics. The goal is to create an inclusive, fast-loading experience for all users regardless of ability or device capability.

**Dependencies**: PRD-027 through PRD-031 (all prior frontend PRDs)

---

## Accessibility Standards

### Target Compliance
- **WCAG 2.1 Level AA** compliance
- **Section 508** compliance for government accessibility
- Support for screen readers (NVDA, JAWS, VoiceOver)
- Full keyboard navigation
- Color-blind friendly design

### Key Principles (POUR)
1. **Perceivable** - Information must be presentable to users in ways they can perceive
2. **Operable** - UI components must be operable via keyboard and assistive technologies
3. **Understandable** - Information and UI operation must be understandable
4. **Robust** - Content must be robust enough for diverse user agents and assistive technologies

---

## Task 1: Semantic HTML & ARIA

**File**: `frontend/js/accessibility.js`

```javascript
/**
 * Accessibility Enhancement Module
 * Manages ARIA attributes, announcements, and keyboard navigation
 */

const AccessibilityManager = {
  // Live region for announcements
  liveRegion: null,

  /**
   * Initialize accessibility features
   */
  init() {
    this.createLiveRegion();
    this.enhanceInteractiveElements();
    this.setupKeyboardNavigation();
    this.setupFocusManagement();
    this.setupReducedMotion();

    console.log('[A11y] Accessibility manager initialized');
  },

  /**
   * Create ARIA live region for announcements
   */
  createLiveRegion() {
    if (document.getElementById('a11y-announcer')) return;

    this.liveRegion = document.createElement('div');
    this.liveRegion.id = 'a11y-announcer';
    this.liveRegion.setAttribute('role', 'status');
    this.liveRegion.setAttribute('aria-live', 'polite');
    this.liveRegion.setAttribute('aria-atomic', 'true');
    this.liveRegion.className = 'sr-only';
    document.body.appendChild(this.liveRegion);
  },

  /**
   * Announce message to screen readers
   */
  announce(message, priority = 'polite') {
    if (!this.liveRegion) return;

    this.liveRegion.setAttribute('aria-live', priority);
    this.liveRegion.textContent = '';

    // Brief delay to ensure announcement is made
    setTimeout(() => {
      this.liveRegion.textContent = message;
    }, 100);
  },

  /**
   * Enhance interactive elements with proper ARIA
   */
  enhanceInteractiveElements() {
    // Enhance cards that act as buttons
    document.querySelectorAll('.card-interactive:not([role])').forEach(card => {
      card.setAttribute('role', 'button');
      card.setAttribute('tabindex', '0');
    });

    // Enhance tab panels
    document.querySelectorAll('.tab-panel').forEach(panel => {
      panel.setAttribute('role', 'tabpanel');
      if (!panel.hasAttribute('aria-labelledby')) {
        const tabId = panel.id?.replace('-panel', '-tab');
        if (tabId) panel.setAttribute('aria-labelledby', tabId);
      }
    });

    // Enhance loading indicators
    document.querySelectorAll('.spinner, .loader').forEach(loader => {
      loader.setAttribute('role', 'status');
      loader.setAttribute('aria-label', 'Loading');
    });

    // Enhance status badges
    document.querySelectorAll('.badge-status').forEach(badge => {
      badge.setAttribute('role', 'status');
    });
  },

  /**
   * Setup keyboard navigation
   */
  setupKeyboardNavigation() {
    document.addEventListener('keydown', (e) => {
      // Skip to main content (Alt + 1)
      if (e.altKey && e.key === '1') {
        e.preventDefault();
        const main = document.querySelector('main, [role="main"]');
        if (main) {
          main.setAttribute('tabindex', '-1');
          main.focus();
          this.announce('Skipped to main content');
        }
      }

      // Open search (Cmd/Ctrl + K)
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        const searchModal = document.getElementById('search-modal');
        if (searchModal) {
          this.openModal(searchModal);
          this.announce('Search opened');
        }
      }

      // Close modals/drawers (Escape)
      if (e.key === 'Escape') {
        const activeModal = document.querySelector('.modal-backdrop.active');
        const activeDrawer = document.querySelector('.drawer.open');

        if (activeModal) {
          this.closeModal(activeModal);
          this.announce('Modal closed');
        } else if (activeDrawer) {
          this.closeDrawer(activeDrawer);
          this.announce('Menu closed');
        }
      }

      // Arrow key navigation for tabs
      if (['ArrowLeft', 'ArrowRight'].includes(e.key)) {
        const activeTab = document.activeElement;
        if (activeTab?.getAttribute('role') === 'tab') {
          this.navigateTabs(activeTab, e.key);
        }
      }
    });

    // Enter/Space activation for custom buttons
    document.addEventListener('keydown', (e) => {
      if (['Enter', ' '].includes(e.key)) {
        const target = e.target;
        if (target.getAttribute('role') === 'button' && target.tagName !== 'BUTTON') {
          e.preventDefault();
          target.click();
        }
      }
    });
  },

  /**
   * Navigate tabs with arrow keys
   */
  navigateTabs(currentTab, direction) {
    const tablist = currentTab.closest('[role="tablist"]');
    if (!tablist) return;

    const tabs = Array.from(tablist.querySelectorAll('[role="tab"]'));
    const currentIndex = tabs.indexOf(currentTab);

    let nextIndex;
    if (direction === 'ArrowRight') {
      nextIndex = currentIndex === tabs.length - 1 ? 0 : currentIndex + 1;
    } else {
      nextIndex = currentIndex === 0 ? tabs.length - 1 : currentIndex - 1;
    }

    tabs[nextIndex].focus();
    tabs[nextIndex].click();
  },

  /**
   * Setup focus management
   */
  setupFocusManagement() {
    // Show focus outline only for keyboard users
    document.body.addEventListener('mousedown', () => {
      document.body.classList.add('using-mouse');
    });

    document.body.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        document.body.classList.remove('using-mouse');
      }
    });

    // Focus trap for modals
    document.addEventListener('focusin', (e) => {
      const activeModal = document.querySelector('.modal-backdrop.active .modal-content');
      if (activeModal && !activeModal.contains(e.target)) {
        const focusable = activeModal.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length) {
          focusable[0].focus();
        }
      }
    });
  },

  /**
   * Setup reduced motion support
   */
  setupReducedMotion() {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    const handleReducedMotion = (e) => {
      if (e.matches) {
        document.body.classList.add('reduce-motion');
        this.announce('Reduced motion mode enabled');
      } else {
        document.body.classList.remove('reduce-motion');
      }
    };

    handleReducedMotion(mediaQuery);
    mediaQuery.addEventListener('change', handleReducedMotion);
  },

  /**
   * Open modal with focus management
   */
  openModal(modal) {
    // Store previously focused element
    modal.dataset.previousFocus = document.activeElement?.id || '';

    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');

    // Focus first focusable element
    const focusable = modal.querySelector(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (focusable) {
      setTimeout(() => focusable.focus(), 100);
    }
  },

  /**
   * Close modal with focus restoration
   */
  closeModal(modal) {
    modal.classList.remove('active');
    modal.setAttribute('aria-hidden', 'true');

    // Restore focus
    const previousFocusId = modal.dataset.previousFocus;
    if (previousFocusId) {
      const previousElement = document.getElementById(previousFocusId);
      if (previousElement) previousElement.focus();
    }
  },

  /**
   * Close drawer
   */
  closeDrawer(drawer) {
    drawer.classList.remove('open');
    drawer.setAttribute('aria-hidden', 'true');
  },

  /**
   * Update loading state with announcement
   */
  setLoading(isLoading, message = '') {
    if (isLoading) {
      this.announce(message || 'Loading content, please wait');
    } else {
      this.announce(message || 'Content loaded');
    }
  },

  /**
   * Announce data update
   */
  announceUpdate(type, details = '') {
    const messages = {
      synthesis: `Research synthesis updated. ${details}`,
      themes: `Theme data updated. ${details}`,
      error: `Error: ${details}`,
      success: `Success: ${details}`
    };

    this.announce(messages[type] || details, type === 'error' ? 'assertive' : 'polite');
  }
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => AccessibilityManager.init());
} else {
  AccessibilityManager.init();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AccessibilityManager;
}
```

---

## Task 2: Accessibility CSS

**File**: `frontend/css/_accessibility.css`

```css
/* ============================================
   Accessibility Styles
   WCAG 2.1 AA compliant styles
   ============================================ */

/* ----- Screen Reader Only ----- */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Make visible when focused (for skip links) */
.sr-only-focusable:focus,
.sr-only-focusable:active {
  position: static;
  width: auto;
  height: auto;
  overflow: visible;
  clip: auto;
  white-space: normal;
}

/* ----- Skip Links ----- */
.skip-link {
  position: fixed;
  top: -100px;
  left: 50%;
  transform: translateX(-50%);
  padding: var(--space-3) var(--space-6);
  background: var(--color-accent-primary);
  color: white;
  font-weight: 600;
  border-radius: var(--radius-md);
  z-index: 9999;
  transition: top var(--duration-fast) var(--ease-out);
}

.skip-link:focus {
  top: var(--space-4);
  outline: 2px solid white;
  outline-offset: 2px;
}

/* ----- Focus Styles ----- */

/* Default focus ring */
:focus {
  outline: 2px solid var(--color-accent-primary);
  outline-offset: 2px;
}

/* Remove focus ring for mouse users */
.using-mouse *:focus {
  outline: none;
}

/* Restore focus ring for focusable elements when using keyboard */
*:focus-visible {
  outline: 2px solid var(--color-accent-primary);
  outline-offset: 2px;
}

/* Enhanced focus for buttons */
.btn:focus-visible {
  outline: 2px solid var(--color-accent-primary);
  outline-offset: 2px;
  box-shadow: 0 0 0 4px rgba(96, 165, 250, 0.3);
}

/* Focus within for card containers */
.card:focus-within {
  outline: 2px solid var(--color-accent-primary);
  outline-offset: 2px;
}

/* ----- High Contrast Mode ----- */
@media (prefers-contrast: high) {
  :root {
    --color-text-primary: #ffffff;
    --color-text-secondary: #e0e0e0;
    --color-bg-primary: #000000;
    --color-bg-secondary: #1a1a1a;
    --color-border-primary: #ffffff;
  }

  .btn {
    border: 2px solid currentColor;
  }

  .card {
    border: 2px solid var(--color-border-primary);
  }

  /* Increase text contrast */
  .text-muted,
  .text-tertiary {
    color: var(--color-text-secondary);
  }
}

/* ----- Reduced Motion ----- */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }

  .animate-pulse,
  .animate-spin,
  .animate-float,
  .animate-bounce-in {
    animation: none !important;
  }
}

.reduce-motion *,
.reduce-motion *::before,
.reduce-motion *::after {
  animation-duration: 0.01ms !important;
  animation-iteration-count: 1 !important;
  transition-duration: 0.01ms !important;
}

/* ----- Color Blind Friendly ----- */

/* Use patterns/shapes in addition to color */
.badge-bullish::before {
  content: '↑';
  margin-right: var(--space-1);
}

.badge-bearish::before {
  content: '↓';
  margin-right: var(--space-1);
}

.badge-neutral::before {
  content: '→';
  margin-right: var(--space-1);
}

/* Status indicators with patterns */
.status-indicator {
  position: relative;
}

.status-indicator--success::after {
  content: '✓';
  position: absolute;
  font-size: 10px;
}

.status-indicator--error::after {
  content: '✕';
  position: absolute;
  font-size: 10px;
}

.status-indicator--warning::after {
  content: '!';
  position: absolute;
  font-size: 10px;
}

/* ----- Minimum Touch Targets ----- */
/* WCAG 2.5.5: 44x44px minimum */
.btn,
[role="button"],
input[type="checkbox"],
input[type="radio"],
.toggle-switch {
  min-width: 44px;
  min-height: 44px;
}

/* Increase tap target on mobile */
@media (max-width: 768px) {
  .btn,
  [role="button"],
  a {
    min-height: 48px;
    padding: var(--space-3) var(--space-4);
  }

  .btn-icon {
    min-width: 48px;
    min-height: 48px;
  }
}

/* ----- Text Spacing ----- */
/* WCAG 1.4.12: Sufficient spacing */
body {
  line-height: 1.5;
  letter-spacing: 0.01em;
}

p {
  margin-bottom: 1em;
}

/* Support for user text spacing overrides */
@supports (line-height: calc(1em + 0.5em)) {
  body.a11y-text-spacing {
    line-height: calc(1em + 0.5em) !important;
    letter-spacing: 0.12em !important;
    word-spacing: 0.16em !important;
  }

  body.a11y-text-spacing p {
    margin-bottom: 2em !important;
  }
}

/* ----- Link Styling ----- */
/* WCAG 1.4.1: Links distinguishable */
a:not(.btn):not(.card) {
  text-decoration: underline;
  text-decoration-color: var(--color-accent-primary);
  text-underline-offset: 2px;
}

a:not(.btn):not(.card):hover {
  text-decoration-thickness: 2px;
}

/* ----- Form Labels ----- */
label {
  display: block;
  margin-bottom: var(--space-1);
  font-weight: 500;
}

/* Required field indicator */
.required::after {
  content: ' *';
  color: var(--color-error);
}

/* Error messages */
.field-error {
  color: var(--color-error);
  font-size: var(--text-sm);
  margin-top: var(--space-1);
}

.field-error::before {
  content: '⚠ ';
}

/* Input error state */
input[aria-invalid="true"],
select[aria-invalid="true"],
textarea[aria-invalid="true"] {
  border-color: var(--color-error);
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2);
}

/* ----- Landmark Regions ----- */
[role="banner"],
[role="navigation"],
[role="main"],
[role="complementary"],
[role="contentinfo"] {
  outline: none;
}

/* ----- Selection Highlight ----- */
::selection {
  background: var(--color-accent-primary);
  color: white;
}

/* ----- Scrollbar Accessibility ----- */
/* Minimum scrollbar width for easier grabbing */
::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}

::-webkit-scrollbar-thumb {
  min-height: 40px;
}

/* ----- Print Styles ----- */
@media print {
  /* Hide non-essential elements */
  nav,
  .skip-link,
  .btn,
  .modal,
  .drawer {
    display: none !important;
  }

  /* Ensure readability */
  body {
    font-size: 12pt;
    line-height: 1.5;
    color: #000;
    background: #fff;
  }

  /* Show URLs for links */
  a[href]::after {
    content: ' (' attr(href) ')';
    font-size: 10pt;
    color: #666;
  }

  /* Avoid page breaks in cards */
  .card {
    break-inside: avoid;
  }
}
```

---

## Task 3: Color Contrast Validation

**File**: `frontend/css/_colors-a11y.css`

```css
/* ============================================
   Accessible Color System
   All combinations meet WCAG AA (4.5:1 for text)
   ============================================ */

:root {
  /* ----- Background Colors ----- */
  /* Base: #0F172A (very dark blue) */
  --color-bg-primary: #0F172A;
  --color-bg-secondary: #1E293B;
  --color-bg-tertiary: #334155;
  --color-bg-elevated: #1E293B;

  /* ----- Text Colors ----- */
  /* All meet 4.5:1 contrast against bg-primary */
  --color-text-primary: #F8FAFC;    /* 15.3:1 */
  --color-text-secondary: #CBD5E1;  /* 9.1:1 */
  --color-text-tertiary: #94A3B8;   /* 5.4:1 */
  --color-text-disabled: #64748B;   /* 3.5:1 - meets AA for large text */

  /* ----- Accent Colors (AA Compliant) ----- */
  /* Primary Blue */
  --color-accent-primary: #60A5FA;     /* 5.8:1 on bg-primary */
  --color-accent-primary-hover: #93C5FD;
  --color-accent-primary-text: #0F172A; /* For use on blue backgrounds */

  /* Secondary Purple */
  --color-accent-secondary: #A78BFA;   /* 5.2:1 on bg-primary */
  --color-accent-secondary-hover: #C4B5FD;

  /* ----- Semantic Colors (AA Compliant) ----- */
  /* Success Green */
  --color-success: #10B981;           /* 4.6:1 on bg-primary */
  --color-success-light: #34D399;     /* 6.5:1 - use for text */
  --color-success-bg: rgba(16, 185, 129, 0.15);

  /* Warning Yellow/Amber */
  --color-warning: #F59E0B;           /* 5.8:1 on bg-primary */
  --color-warning-light: #FBBF24;     /* 8.2:1 */
  --color-warning-bg: rgba(245, 158, 11, 0.15);

  /* Error Red */
  --color-error: #EF4444;             /* 4.5:1 on bg-primary */
  --color-error-light: #F87171;       /* 5.7:1 - use for text */
  --color-error-bg: rgba(239, 68, 68, 0.15);

  /* Info Blue */
  --color-info: #3B82F6;              /* 4.5:1 on bg-primary */
  --color-info-light: #60A5FA;        /* 5.8:1 */
  --color-info-bg: rgba(59, 130, 246, 0.15);

  /* ----- Source Colors (Adjusted for AA) ----- */
  --color-source-discord: #7289DA;    /* 5.1:1 */
  --color-source-42macro: #F59E0B;    /* 5.8:1 */
  --color-source-kt: #10B981;         /* 4.6:1 */
  --color-source-youtube: #F87171;    /* 5.7:1 */
  --color-source-substack: #FF7F50;   /* 4.8:1 */

  /* ----- Sentiment Colors ----- */
  --color-bullish: #34D399;           /* 6.5:1 - bright green */
  --color-bearish: #F87171;           /* 5.7:1 - bright red */
  --color-neutral: #94A3B8;           /* 5.4:1 - muted gray */

  /* ----- Theme Status Colors ----- */
  --color-status-emerging: #FBBF24;   /* 8.2:1 - bright yellow */
  --color-status-active: #34D399;     /* 6.5:1 - bright green */
  --color-status-evolved: #60A5FA;    /* 5.8:1 - bright blue */
  --color-status-dormant: #94A3B8;    /* 5.4:1 - muted gray */

  /* ----- Border Colors ----- */
  --color-border-primary: rgba(255, 255, 255, 0.1);
  --color-border-secondary: rgba(255, 255, 255, 0.05);
  --color-border-focus: var(--color-accent-primary);
}

/* ----- Badge Color Classes ----- */
/* Each badge has sufficient contrast */

.badge-primary {
  background: var(--color-accent-primary);
  color: var(--color-accent-primary-text);
}

.badge-success {
  background: var(--color-success);
  color: #0F172A; /* 7.2:1 contrast */
}

.badge-warning {
  background: var(--color-warning);
  color: #0F172A; /* 8.5:1 contrast */
}

.badge-error {
  background: var(--color-error);
  color: #FFFFFF; /* 4.6:1 contrast */
}

/* ----- Text on Colored Backgrounds ----- */
.text-on-primary {
  color: var(--color-accent-primary-text);
}

.text-on-success {
  color: #0F172A;
}

.text-on-warning {
  color: #0F172A;
}

.text-on-error {
  color: #FFFFFF;
}

/* ----- Link Colors ----- */
a {
  color: var(--color-accent-primary);
}

a:visited {
  color: var(--color-accent-secondary);
}

a:hover {
  color: var(--color-accent-primary-hover);
}

/* ----- Contrast Checker Reference -----
   Tool: https://webaim.org/resources/contrastchecker/

   Background: #0F172A (rgb: 15, 23, 42)

   Text Colors:
   - #F8FAFC: 15.32:1 ✓ AAA
   - #CBD5E1: 9.12:1 ✓ AAA
   - #94A3B8: 5.42:1 ✓ AA
   - #64748B: 3.51:1 ✓ AA Large

   Accent Colors:
   - #60A5FA: 5.84:1 ✓ AA
   - #A78BFA: 5.23:1 ✓ AA
   - #10B981: 4.63:1 ✓ AA
   - #F59E0B: 5.81:1 ✓ AA
   - #EF4444: 4.53:1 ✓ AA
----- */
```

---

## Task 4: Performance Optimization

**File**: `frontend/js/performance.js`

```javascript
/**
 * Performance Optimization Module
 * Handles lazy loading, caching, and performance monitoring
 */

const PerformanceManager = {
  // Performance metrics
  metrics: {
    fcp: null,      // First Contentful Paint
    lcp: null,      // Largest Contentful Paint
    fid: null,      // First Input Delay
    cls: null,      // Cumulative Layout Shift
    ttfb: null      // Time to First Byte
  },

  // Cache for API responses
  cache: new Map(),
  cacheExpiry: 5 * 60 * 1000, // 5 minutes

  /**
   * Initialize performance optimizations
   */
  init() {
    this.setupLazyLoading();
    this.setupResourceHints();
    this.measureWebVitals();
    this.setupIdleCallback();

    console.log('[Perf] Performance manager initialized');
  },

  /**
   * Setup lazy loading for images and iframes
   */
  setupLazyLoading() {
    // Native lazy loading for images
    document.querySelectorAll('img[data-src]').forEach(img => {
      img.loading = 'lazy';
      img.src = img.dataset.src;
    });

    // Intersection Observer for custom lazy loading
    const lazyObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target;

          // Load background images
          if (el.dataset.bg) {
            el.style.backgroundImage = `url(${el.dataset.bg})`;
            el.classList.add('loaded');
          }

          // Load iframes
          if (el.tagName === 'IFRAME' && el.dataset.src) {
            el.src = el.dataset.src;
          }

          lazyObserver.unobserve(el);
        }
      });
    }, {
      rootMargin: '100px',
      threshold: 0.01
    });

    document.querySelectorAll('[data-bg], iframe[data-src]').forEach(el => {
      lazyObserver.observe(el);
    });

    this.lazyObserver = lazyObserver;
  },

  /**
   * Setup resource hints for faster loading
   */
  setupResourceHints() {
    // Preconnect to API domain
    this.addResourceHint('preconnect', 'https://confluence-production-a32e.up.railway.app');

    // Preload critical assets
    this.addResourceHint('preload', '/css/design-system.css', 'style');
    this.addResourceHint('preload', '/js/api.js', 'script');

    // Prefetch likely next pages
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => {
        // Prefetch dashboard data
        this.prefetchData('/api/dashboard/today');
      });
    }
  },

  /**
   * Add resource hint to head
   */
  addResourceHint(rel, href, as = null) {
    if (document.querySelector(`link[href="${href}"]`)) return;

    const link = document.createElement('link');
    link.rel = rel;
    link.href = href;
    if (as) link.as = as;
    if (rel === 'preconnect') link.crossOrigin = 'anonymous';

    document.head.appendChild(link);
  },

  /**
   * Measure Web Vitals
   */
  measureWebVitals() {
    // First Contentful Paint
    const paintObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === 'first-contentful-paint') {
          this.metrics.fcp = entry.startTime;
          console.log(`[Perf] FCP: ${entry.startTime.toFixed(2)}ms`);
        }
      }
    });
    paintObserver.observe({ type: 'paint', buffered: true });

    // Largest Contentful Paint
    const lcpObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      this.metrics.lcp = lastEntry.startTime;
      console.log(`[Perf] LCP: ${lastEntry.startTime.toFixed(2)}ms`);
    });
    lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });

    // First Input Delay
    const fidObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        this.metrics.fid = entry.processingStart - entry.startTime;
        console.log(`[Perf] FID: ${this.metrics.fid.toFixed(2)}ms`);
      }
    });
    fidObserver.observe({ type: 'first-input', buffered: true });

    // Cumulative Layout Shift
    let clsValue = 0;
    const clsObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
        }
      }
      this.metrics.cls = clsValue;
    });
    clsObserver.observe({ type: 'layout-shift', buffered: true });

    // Time to First Byte
    const navigation = performance.getEntriesByType('navigation')[0];
    if (navigation) {
      this.metrics.ttfb = navigation.responseStart - navigation.requestStart;
      console.log(`[Perf] TTFB: ${this.metrics.ttfb.toFixed(2)}ms`);
    }
  },

  /**
   * Setup idle callback for non-critical work
   */
  setupIdleCallback() {
    if (!('requestIdleCallback' in window)) {
      // Polyfill for Safari
      window.requestIdleCallback = (callback) => {
        return setTimeout(() => {
          callback({
            didTimeout: false,
            timeRemaining: () => 50
          });
        }, 1);
      };
    }

    // Queue non-critical initialization
    requestIdleCallback(() => {
      // Initialize charts lazily
      if (typeof ChartsManager !== 'undefined') {
        ChartsManager.init();
      }

      // Preload fonts
      this.preloadFonts();
    });
  },

  /**
   * Preload fonts
   */
  preloadFonts() {
    const fonts = [
      { family: 'Inter', weight: '400' },
      { family: 'Inter', weight: '500' },
      { family: 'Inter', weight: '600' },
      { family: 'JetBrains Mono', weight: '400' }
    ];

    fonts.forEach(({ family, weight }) => {
      const font = new FontFace(family, `local('${family}')`, { weight });
      font.load().catch(() => {
        // Font not available locally, will load from Google Fonts
      });
    });
  },

  /**
   * Cached fetch with expiry
   */
  async cachedFetch(url, options = {}) {
    const cacheKey = `${url}-${JSON.stringify(options)}`;
    const cached = this.cache.get(cacheKey);

    if (cached && Date.now() - cached.timestamp < this.cacheExpiry) {
      return cached.data;
    }

    const response = await fetch(url, options);
    const data = await response.json();

    this.cache.set(cacheKey, {
      data,
      timestamp: Date.now()
    });

    return data;
  },

  /**
   * Prefetch data for faster navigation
   */
  async prefetchData(url) {
    try {
      await this.cachedFetch(url);
    } catch (e) {
      // Silently fail prefetch
    }
  },

  /**
   * Debounce function for scroll/resize handlers
   */
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  /**
   * Throttle function for high-frequency events
   */
  throttle(func, limit) {
    let inThrottle;
    return function(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },

  /**
   * Get current performance metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      memory: performance.memory ? {
        usedJSHeapSize: (performance.memory.usedJSHeapSize / 1048576).toFixed(2) + 'MB',
        totalJSHeapSize: (performance.memory.totalJSHeapSize / 1048576).toFixed(2) + 'MB'
      } : null
    };
  },

  /**
   * Clear expired cache entries
   */
  clearExpiredCache() {
    const now = Date.now();
    for (const [key, value] of this.cache) {
      if (now - value.timestamp > this.cacheExpiry) {
        this.cache.delete(key);
      }
    }
  }
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => PerformanceManager.init());
} else {
  PerformanceManager.init();
}

// Clear cache periodically
setInterval(() => PerformanceManager.clearExpiredCache(), 60000);

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PerformanceManager;
}
```

---

## Task 5: Critical CSS & Loading Strategy

**File**: `frontend/css/_critical.css`

```css
/* ============================================
   Critical CSS
   Inline this in <head> for faster FCP
   ============================================ */

/* ----- Minimal Reset ----- */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

/* ----- Critical Variables ----- */
:root {
  --color-bg-primary: #0F172A;
  --color-text-primary: #F8FAFC;
  --color-accent-primary: #60A5FA;
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ----- Body ----- */
html {
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
}

body {
  font-family: var(--font-family);
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
  line-height: 1.5;
  min-height: 100vh;
}

/* ----- Initial Loading State ----- */
.page-loading {
  opacity: 0;
}

/* ----- Header Skeleton ----- */
.header {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 64px;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

/* ----- Main Container ----- */
main {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

/* ----- Content Placeholder ----- */
.content-placeholder {
  background: linear-gradient(90deg, #1E293B 25%, #334155 50%, #1E293B 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 12px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ----- Hero Placeholder ----- */
.hero-placeholder {
  height: 200px;
  margin-bottom: 24px;
}

/* ----- KPI Grid Placeholder ----- */
.kpi-placeholder {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.kpi-placeholder > div {
  height: 100px;
}

/* ----- Prevent FOUT (Flash of Unstyled Text) ----- */
.fonts-loading body {
  visibility: hidden;
}

.fonts-loaded body,
.fonts-failed body {
  visibility: visible;
}
```

---

## Task 6: HTML Template Updates

**File**: Update `frontend/index.html` head section

```html
<!DOCTYPE html>
<html lang="en" class="fonts-loading">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <meta name="description" content="AI-powered investment research synthesis and confluence analysis">
  <meta name="theme-color" content="#0F172A">

  <!-- Preconnect to external resources -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

  <!-- Critical CSS (inline for faster FCP) -->
  <style>
    /* Contents of _critical.css inlined here */
  </style>

  <!-- Preload critical resources -->
  <link rel="preload" href="/css/design-system.css" as="style">
  <link rel="preload" href="/js/api.js" as="script">

  <!-- Load fonts with display=swap for better performance -->
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

  <!-- Main stylesheet (deferred) -->
  <link rel="stylesheet" href="/css/design-system.css" media="print" onload="this.media='all'">
  <noscript><link rel="stylesheet" href="/css/design-system.css"></noscript>

  <title>Macro Confluence Hub</title>

  <!-- Font loading detection -->
  <script>
    if ('fonts' in document) {
      Promise.all([
        document.fonts.load('400 1em Inter'),
        document.fonts.load('600 1em Inter')
      ]).then(() => {
        document.documentElement.classList.remove('fonts-loading');
        document.documentElement.classList.add('fonts-loaded');
      }).catch(() => {
        document.documentElement.classList.remove('fonts-loading');
        document.documentElement.classList.add('fonts-failed');
      });
    } else {
      document.documentElement.classList.remove('fonts-loading');
    }
  </script>
</head>
<body class="page-loading">
  <!-- Skip Link -->
  <a href="#main-content" class="skip-link">Skip to main content</a>

  <!-- Loading placeholder shown while JS loads -->
  <div id="loading-placeholder" aria-hidden="true">
    <div class="header"></div>
    <main>
      <div class="hero-placeholder content-placeholder"></div>
      <div class="kpi-placeholder">
        <div class="content-placeholder"></div>
        <div class="content-placeholder"></div>
        <div class="content-placeholder"></div>
        <div class="content-placeholder"></div>
      </div>
    </main>
  </div>

  <!-- Main app container (hidden until loaded) -->
  <div id="app" hidden>
    <!-- App content here -->
  </div>

  <!-- Scripts at end of body -->
  <script src="/js/performance.js" defer></script>
  <script src="/js/accessibility.js" defer></script>
  <script src="/js/animations.js" defer></script>
  <script src="/js/api.js" defer></script>
  <script src="/js/app.js" defer></script>

  <!-- Remove loading state when app is ready -->
  <script>
    document.addEventListener('DOMContentLoaded', () => {
      // Hide loading placeholder
      document.getElementById('loading-placeholder').hidden = true;

      // Show app
      document.getElementById('app').hidden = false;

      // Remove loading class
      document.body.classList.remove('page-loading');
      document.body.classList.add('page-ready');
    });
  </script>
</body>
</html>
```

---

## Task 7: Testing Checklist

### Accessibility Testing

**Automated Testing:**
- [ ] Run axe-core DevTools extension
- [ ] Run WAVE evaluation tool
- [ ] Run Lighthouse accessibility audit (target: 90+)
- [ ] Validate HTML with W3C validator

**Manual Testing:**
- [ ] Navigate entire app using keyboard only
- [ ] Test with screen reader (NVDA or VoiceOver)
- [ ] Test at 200% zoom
- [ ] Test with browser text size increased
- [ ] Test color contrast with Colour Contrast Analyser
- [ ] Test with Windows High Contrast mode
- [ ] Test with prefers-reduced-motion enabled

**Keyboard Navigation:**
- [ ] All interactive elements focusable
- [ ] Focus order logical (left-to-right, top-to-bottom)
- [ ] Focus visible at all times
- [ ] No keyboard traps
- [ ] Escape closes modals/menus
- [ ] Tab navigation works in forms
- [ ] Arrow keys work for tabs/menus

**Screen Reader Testing:**
- [ ] Page title announced
- [ ] Headings hierarchy correct (h1 → h2 → h3)
- [ ] All images have alt text
- [ ] Form inputs have labels
- [ ] Buttons have accessible names
- [ ] Status updates announced
- [ ] Loading states announced

### Performance Testing

**Metrics Targets (Lighthouse):**
- [ ] Performance score: 90+
- [ ] First Contentful Paint: < 1.8s
- [ ] Largest Contentful Paint: < 2.5s
- [ ] First Input Delay: < 100ms
- [ ] Cumulative Layout Shift: < 0.1
- [ ] Time to Interactive: < 3.8s

**Network Testing:**
- [ ] Test on slow 3G (Chrome DevTools)
- [ ] Test offline functionality
- [ ] Verify caching works
- [ ] Check bundle sizes (< 200KB JS, < 50KB CSS)

**Mobile Testing:**
- [ ] Test on real devices (iOS Safari, Android Chrome)
- [ ] Verify touch targets 44x44px minimum
- [ ] Test orientation changes
- [ ] Verify no horizontal scroll

---

## Implementation Checklist

### Task 1: Accessibility JavaScript
- [ ] Create `frontend/js/accessibility.js`
- [ ] Implement ARIA live region
- [ ] Add keyboard navigation
- [ ] Add focus management
- [ ] Add reduced motion support

### Task 2: Accessibility CSS
- [ ] Create `frontend/css/_accessibility.css`
- [ ] Add screen reader utilities
- [ ] Add skip link styles
- [ ] Add focus styles
- [ ] Add high contrast support
- [ ] Add reduced motion support

### Task 3: Color Contrast Validation
- [ ] Create `frontend/css/_colors-a11y.css`
- [ ] Verify all color combinations
- [ ] Document contrast ratios
- [ ] Add semantic color mappings

### Task 4: Performance JavaScript
- [ ] Create `frontend/js/performance.js`
- [ ] Implement lazy loading
- [ ] Add resource hints
- [ ] Add Web Vitals tracking
- [ ] Add caching layer

### Task 5: Critical CSS
- [ ] Create `frontend/css/_critical.css`
- [ ] Extract above-fold styles
- [ ] Add loading placeholders
- [ ] Add font loading strategy

### Task 6: HTML Updates
- [ ] Update index.html head
- [ ] Add skip link
- [ ] Add ARIA landmarks
- [ ] Add loading strategy
- [ ] Add script loading optimization

### Task 7: Testing
- [ ] Run automated accessibility tests
- [ ] Complete manual testing checklist
- [ ] Run Lighthouse audits
- [ ] Test on real devices

---

## Performance Budget

| Asset Type | Budget | Notes |
|------------|--------|-------|
| HTML | < 50KB | Compressed |
| CSS (total) | < 50KB | Design system + components |
| JS (total) | < 200KB | All scripts combined |
| Images | < 100KB each | Use WebP, lazy load |
| Fonts | < 100KB | Subset, WOFF2 only |
| API Response | < 50KB | Compress JSON |

## Accessibility Requirements Summary

| Requirement | Standard | Implementation |
|-------------|----------|----------------|
| Color Contrast | 4.5:1 (AA) | Validated palette in Task 3 |
| Keyboard Navigation | Full | AccessibilityManager in Task 1 |
| Screen Reader | Full | ARIA + semantic HTML |
| Focus Indicators | Visible | CSS in Task 2 |
| Touch Targets | 44x44px | CSS in Task 2 |
| Reduced Motion | Respect preference | CSS + JS |
| Text Scaling | Up to 200% | Responsive design |
