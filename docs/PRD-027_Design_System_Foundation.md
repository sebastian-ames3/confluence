# PRD-027: Design System Foundation

## Overview

Establish a comprehensive design system foundation with CSS custom properties, typography scale, color palette, spacing system, and core utilities. This forms the base layer for all subsequent UI/UX improvements.

**Status**: Proposed
**Priority**: Critical (Prerequisite for all other UI PRDs)
**Depends On**: None
**Blocks**: PRD-028, PRD-029, PRD-030, PRD-031

---

## Goals

1. Create a single source of truth for all design tokens
2. Enable consistent theming across the application
3. Support future light/dark mode toggle
4. Improve maintainability of CSS codebase
5. Establish foundation for glassmorphism and neumorphism effects

---

## Technical Specification

### File Structure

```
frontend/
├── css/
│   ├── design-system/
│   │   ├── _tokens.css        # All CSS custom properties
│   │   ├── _typography.css    # Font definitions and text utilities
│   │   ├── _colors.css        # Color palette and semantic colors
│   │   ├── _spacing.css       # Spacing scale and utilities
│   │   ├── _effects.css       # Shadows, blurs, gradients
│   │   └── _reset.css         # Modern CSS reset
│   ├── design-system.css      # Imports all design system files
│   ├── style.css              # (Updated to use design system)
│   └── mobile.css             # (Updated to use design system)
```

---

## Implementation Tasks

### Task 1: Create Design Tokens File (`_tokens.css`)

**File**: `frontend/css/design-system/_tokens.css`

```css
/**
 * Design Tokens - Single source of truth for all design values
 * Macro Confluence Hub Design System v2.0
 */

:root {
  /* ============================================
     COLOR TOKENS - Base Palette
     ============================================ */

  /* Neutrals */
  --color-black: #000000;
  --color-white: #ffffff;

  --color-gray-50: #fafafa;
  --color-gray-100: #f5f5f5;
  --color-gray-200: #e5e5e5;
  --color-gray-300: #d4d4d4;
  --color-gray-400: #a3a3a3;
  --color-gray-500: #737373;
  --color-gray-600: #525252;
  --color-gray-700: #404040;
  --color-gray-800: #262626;
  --color-gray-900: #171717;
  --color-gray-950: #0a0a0a;

  /* Primary - Blue */
  --color-primary-50: #eff6ff;
  --color-primary-100: #dbeafe;
  --color-primary-200: #bfdbfe;
  --color-primary-300: #93c5fd;
  --color-primary-400: #60a5fa;
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;
  --color-primary-700: #1d4ed8;
  --color-primary-800: #1e40af;
  --color-primary-900: #1e3a8a;

  /* Success - Green */
  --color-success-50: #ecfdf5;
  --color-success-100: #d1fae5;
  --color-success-200: #a7f3d0;
  --color-success-300: #6ee7b7;
  --color-success-400: #34d399;
  --color-success-500: #10b981;
  --color-success-600: #059669;
  --color-success-700: #047857;
  --color-success-800: #065f46;
  --color-success-900: #064e3b;

  /* Warning - Amber */
  --color-warning-50: #fffbeb;
  --color-warning-100: #fef3c7;
  --color-warning-200: #fde68a;
  --color-warning-300: #fcd34d;
  --color-warning-400: #fbbf24;
  --color-warning-500: #f59e0b;
  --color-warning-600: #d97706;
  --color-warning-700: #b45309;
  --color-warning-800: #92400e;
  --color-warning-900: #78350f;

  /* Danger - Red */
  --color-danger-50: #fef2f2;
  --color-danger-100: #fee2e2;
  --color-danger-200: #fecaca;
  --color-danger-300: #fca5a5;
  --color-danger-400: #f87171;
  --color-danger-500: #ef4444;
  --color-danger-600: #dc2626;
  --color-danger-700: #b91c1c;
  --color-danger-800: #991b1b;
  --color-danger-900: #7f1d1d;

  /* Purple (for accents) */
  --color-purple-400: #a78bfa;
  --color-purple-500: #8b5cf6;
  --color-purple-600: #7c3aed;

  /* ============================================
     SPACING TOKENS
     ============================================ */
  --space-0: 0;
  --space-px: 1px;
  --space-0-5: 0.125rem;  /* 2px */
  --space-1: 0.25rem;     /* 4px */
  --space-1-5: 0.375rem;  /* 6px */
  --space-2: 0.5rem;      /* 8px */
  --space-2-5: 0.625rem;  /* 10px */
  --space-3: 0.75rem;     /* 12px */
  --space-3-5: 0.875rem;  /* 14px */
  --space-4: 1rem;        /* 16px */
  --space-5: 1.25rem;     /* 20px */
  --space-6: 1.5rem;      /* 24px */
  --space-7: 1.75rem;     /* 28px */
  --space-8: 2rem;        /* 32px */
  --space-9: 2.25rem;     /* 36px */
  --space-10: 2.5rem;     /* 40px */
  --space-11: 2.75rem;    /* 44px */
  --space-12: 3rem;       /* 48px */
  --space-14: 3.5rem;     /* 56px */
  --space-16: 4rem;       /* 64px */
  --space-20: 5rem;       /* 80px */
  --space-24: 6rem;       /* 96px */
  --space-28: 7rem;       /* 112px */
  --space-32: 8rem;       /* 128px */

  /* ============================================
     TYPOGRAPHY TOKENS
     ============================================ */

  /* Font Families */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace;

  /* Font Sizes */
  --text-xs: 0.75rem;     /* 12px */
  --text-sm: 0.875rem;    /* 14px */
  --text-base: 1rem;      /* 16px */
  --text-lg: 1.125rem;    /* 18px */
  --text-xl: 1.25rem;     /* 20px */
  --text-2xl: 1.5rem;     /* 24px */
  --text-3xl: 1.875rem;   /* 30px */
  --text-4xl: 2.25rem;    /* 36px */
  --text-5xl: 3rem;       /* 48px */
  --text-6xl: 3.75rem;    /* 60px */

  /* Line Heights */
  --leading-none: 1;
  --leading-tight: 1.25;
  --leading-snug: 1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
  --leading-loose: 2;

  /* Font Weights */
  --font-thin: 100;
  --font-extralight: 200;
  --font-light: 300;
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
  --font-extrabold: 800;
  --font-black: 900;

  /* Letter Spacing */
  --tracking-tighter: -0.05em;
  --tracking-tight: -0.025em;
  --tracking-normal: 0;
  --tracking-wide: 0.025em;
  --tracking-wider: 0.05em;
  --tracking-widest: 0.1em;

  /* ============================================
     BORDER RADIUS TOKENS
     ============================================ */
  --radius-none: 0;
  --radius-sm: 0.25rem;   /* 4px */
  --radius-md: 0.375rem;  /* 6px */
  --radius-lg: 0.5rem;    /* 8px */
  --radius-xl: 0.75rem;   /* 12px */
  --radius-2xl: 1rem;     /* 16px */
  --radius-3xl: 1.5rem;   /* 24px */
  --radius-full: 9999px;

  /* ============================================
     SHADOW TOKENS
     ============================================ */
  --shadow-xs: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-sm: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
  --shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);
  --shadow-inner: inset 0 2px 4px 0 rgb(0 0 0 / 0.05);

  /* Dark mode shadows (more prominent) */
  --shadow-dark-sm: 0 2px 4px 0 rgb(0 0 0 / 0.3);
  --shadow-dark-md: 0 4px 8px 0 rgb(0 0 0 / 0.4);
  --shadow-dark-lg: 0 8px 16px 0 rgb(0 0 0 / 0.5);
  --shadow-dark-xl: 0 16px 32px 0 rgb(0 0 0 / 0.6);

  /* ============================================
     TRANSITION TOKENS
     ============================================ */
  --duration-75: 75ms;
  --duration-100: 100ms;
  --duration-150: 150ms;
  --duration-200: 200ms;
  --duration-300: 300ms;
  --duration-500: 500ms;
  --duration-700: 700ms;
  --duration-1000: 1000ms;

  --ease-linear: linear;
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-bounce: cubic-bezier(0.68, -0.55, 0.27, 1.55);
  --ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);

  /* ============================================
     Z-INDEX TOKENS
     ============================================ */
  --z-0: 0;
  --z-10: 10;
  --z-20: 20;
  --z-30: 30;
  --z-40: 40;
  --z-50: 50;
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-fixed: 300;
  --z-modal-backdrop: 400;
  --z-modal: 500;
  --z-popover: 600;
  --z-tooltip: 700;
  --z-toast: 800;

  /* ============================================
     BREAKPOINT TOKENS (for reference in JS)
     ============================================ */
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
  --breakpoint-2xl: 1536px;
}
```

**Acceptance Criteria**:
- [ ] All token values are defined
- [ ] Tokens follow consistent naming convention
- [ ] Comments explain token categories
- [ ] File is importable without errors

---

### Task 2: Create Semantic Color Mappings (`_colors.css`)

**File**: `frontend/css/design-system/_colors.css`

```css
/**
 * Semantic Color Mappings
 * Maps raw color tokens to semantic usage
 */

:root {
  /* ============================================
     SEMANTIC COLORS - Dark Theme (Default)
     ============================================ */

  /* Background Layers */
  --bg-base: var(--color-gray-950);
  --bg-surface: var(--color-gray-900);
  --bg-elevated: var(--color-gray-800);
  --bg-overlay: rgba(0, 0, 0, 0.8);

  /* Glassmorphism Backgrounds */
  --bg-glass: rgba(255, 255, 255, 0.03);
  --bg-glass-hover: rgba(255, 255, 255, 0.06);
  --bg-glass-active: rgba(255, 255, 255, 0.08);
  --bg-glass-border: rgba(255, 255, 255, 0.08);

  /* Text Colors */
  --text-primary: var(--color-gray-50);
  --text-secondary: var(--color-gray-400);
  --text-muted: var(--color-gray-500);
  --text-disabled: var(--color-gray-600);
  --text-inverse: var(--color-gray-900);

  /* Border Colors */
  --border-default: var(--color-gray-800);
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-medium: rgba(255, 255, 255, 0.12);
  --border-strong: rgba(255, 255, 255, 0.18);
  --border-focus: var(--color-primary-500);

  /* Interactive Colors */
  --interactive-default: var(--color-primary-500);
  --interactive-hover: var(--color-primary-400);
  --interactive-active: var(--color-primary-600);
  --interactive-disabled: var(--color-gray-600);

  /* Status Colors */
  --status-success: var(--color-success-500);
  --status-success-bg: rgba(16, 185, 129, 0.1);
  --status-success-border: rgba(16, 185, 129, 0.3);

  --status-warning: var(--color-warning-500);
  --status-warning-bg: rgba(245, 158, 11, 0.1);
  --status-warning-border: rgba(245, 158, 11, 0.3);

  --status-danger: var(--color-danger-500);
  --status-danger-bg: rgba(239, 68, 68, 0.1);
  --status-danger-border: rgba(239, 68, 68, 0.3);

  --status-info: var(--color-primary-500);
  --status-info-bg: rgba(59, 130, 246, 0.1);
  --status-info-border: rgba(59, 130, 246, 0.3);

  /* Sentiment Colors (for financial data) */
  --sentiment-bullish: var(--color-success-500);
  --sentiment-bullish-bg: rgba(16, 185, 129, 0.15);
  --sentiment-bearish: var(--color-danger-500);
  --sentiment-bearish-bg: rgba(239, 68, 68, 0.15);
  --sentiment-neutral: var(--color-gray-400);
  --sentiment-neutral-bg: rgba(163, 163, 163, 0.15);

  /* Source Brand Colors */
  --source-youtube: #ff0000;
  --source-youtube-bg: rgba(255, 0, 0, 0.1);
  --source-discord: #5865f2;
  --source-discord-bg: rgba(88, 101, 242, 0.1);
  --source-substack: #ff6719;
  --source-substack-bg: rgba(255, 103, 25, 0.1);
  --source-42macro: var(--color-primary-500);
  --source-42macro-bg: rgba(59, 130, 246, 0.1);
  --source-kt-technical: #eab308;
  --source-kt-technical-bg: rgba(234, 179, 8, 0.1);

  /* Gradients */
  --gradient-primary: linear-gradient(135deg, var(--color-primary-500) 0%, var(--color-purple-500) 100%);
  --gradient-success: linear-gradient(135deg, var(--color-success-500) 0%, var(--color-success-600) 100%);
  --gradient-warning: linear-gradient(135deg, var(--color-warning-500) 0%, var(--color-warning-600) 100%);
  --gradient-danger: linear-gradient(135deg, var(--color-danger-500) 0%, var(--color-danger-600) 100%);
  --gradient-surface: linear-gradient(180deg, var(--bg-surface) 0%, var(--bg-base) 100%);
  --gradient-glow: radial-gradient(ellipse at center, var(--color-primary-500) 0%, transparent 70%);

  /* Glow Effects */
  --glow-primary: 0 0 20px rgba(59, 130, 246, 0.4);
  --glow-success: 0 0 20px rgba(16, 185, 129, 0.4);
  --glow-warning: 0 0 20px rgba(245, 158, 11, 0.4);
  --glow-danger: 0 0 20px rgba(239, 68, 68, 0.4);
}

/* ============================================
   LIGHT THEME (Future Implementation)
   ============================================ */
[data-theme="light"] {
  --bg-base: var(--color-gray-50);
  --bg-surface: var(--color-white);
  --bg-elevated: var(--color-gray-100);
  --bg-overlay: rgba(0, 0, 0, 0.5);

  --bg-glass: rgba(255, 255, 255, 0.7);
  --bg-glass-hover: rgba(255, 255, 255, 0.8);
  --bg-glass-active: rgba(255, 255, 255, 0.9);
  --bg-glass-border: rgba(0, 0, 0, 0.08);

  --text-primary: var(--color-gray-900);
  --text-secondary: var(--color-gray-600);
  --text-muted: var(--color-gray-500);
  --text-disabled: var(--color-gray-400);
  --text-inverse: var(--color-white);

  --border-default: var(--color-gray-200);
  --border-subtle: rgba(0, 0, 0, 0.06);
  --border-medium: rgba(0, 0, 0, 0.12);
  --border-strong: rgba(0, 0, 0, 0.18);
}
```

**Acceptance Criteria**:
- [ ] All semantic colors mapped to raw tokens
- [ ] Dark theme is default
- [ ] Light theme variables prepared (commented for future)
- [ ] Source brand colors defined
- [ ] Gradient definitions included

---

### Task 3: Create Typography System (`_typography.css`)

**File**: `frontend/css/design-system/_typography.css`

```css
/**
 * Typography System
 * Font imports, text styles, and utilities
 */

/* ============================================
   FONT IMPORTS
   ============================================ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Optional: JetBrains Mono for code/numbers */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ============================================
   BASE TYPOGRAPHY
   ============================================ */
html {
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

body {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  font-weight: var(--font-normal);
  line-height: var(--leading-normal);
  color: var(--text-primary);
}

/* ============================================
   HEADINGS
   ============================================ */
h1, h2, h3, h4, h5, h6 {
  font-weight: var(--font-semibold);
  line-height: var(--leading-tight);
  color: var(--text-primary);
  margin: 0;
}

.heading-1, h1 {
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  letter-spacing: var(--tracking-tight);
}

.heading-2, h2 {
  font-size: var(--text-3xl);
  font-weight: var(--font-semibold);
  letter-spacing: var(--tracking-tight);
}

.heading-3, h3 {
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
}

.heading-4, h4 {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
}

.heading-5, h5 {
  font-size: var(--text-lg);
  font-weight: var(--font-medium);
}

.heading-6, h6 {
  font-size: var(--text-base);
  font-weight: var(--font-medium);
}

/* ============================================
   DISPLAY TEXT (Hero sections)
   ============================================ */
.display-large {
  font-size: var(--text-6xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-none);
  letter-spacing: var(--tracking-tighter);
}

.display-medium {
  font-size: var(--text-5xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  letter-spacing: var(--tracking-tight);
}

.display-small {
  font-size: var(--text-4xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-tight);
  letter-spacing: var(--tracking-tight);
}

/* ============================================
   BODY TEXT
   ============================================ */
.body-large {
  font-size: var(--text-lg);
  line-height: var(--leading-relaxed);
}

.body-base {
  font-size: var(--text-base);
  line-height: var(--leading-normal);
}

.body-small {
  font-size: var(--text-sm);
  line-height: var(--leading-normal);
}

/* ============================================
   LABELS & CAPTIONS
   ============================================ */
.label {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--text-muted);
}

.caption {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  line-height: var(--leading-normal);
}

.overline {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  text-transform: uppercase;
  letter-spacing: var(--tracking-widest);
  color: var(--text-muted);
}

/* ============================================
   MONOSPACE / DATA
   ============================================ */
.mono {
  font-family: var(--font-mono);
}

.data-value {
  font-family: var(--font-mono);
  font-weight: var(--font-semibold);
  font-variant-numeric: tabular-nums;
}

.data-large {
  font-family: var(--font-mono);
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  font-variant-numeric: tabular-nums;
}

/* ============================================
   TEXT UTILITIES
   ============================================ */
.text-primary { color: var(--text-primary); }
.text-secondary { color: var(--text-secondary); }
.text-muted { color: var(--text-muted); }
.text-disabled { color: var(--text-disabled); }

.text-success { color: var(--status-success); }
.text-warning { color: var(--status-warning); }
.text-danger { color: var(--status-danger); }
.text-info { color: var(--status-info); }

.text-bullish { color: var(--sentiment-bullish); }
.text-bearish { color: var(--sentiment-bearish); }
.text-neutral { color: var(--sentiment-neutral); }

/* Alignment */
.text-left { text-align: left; }
.text-center { text-align: center; }
.text-right { text-align: right; }

/* Weight */
.font-normal { font-weight: var(--font-normal); }
.font-medium { font-weight: var(--font-medium); }
.font-semibold { font-weight: var(--font-semibold); }
.font-bold { font-weight: var(--font-bold); }

/* Truncation */
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

**Acceptance Criteria**:
- [ ] Google Fonts imported (Inter, JetBrains Mono)
- [ ] Heading hierarchy defined
- [ ] Display text classes for hero sections
- [ ] Body text variations
- [ ] Label and caption styles
- [ ] Monospace styles for data
- [ ] Text utility classes

---

### Task 4: Create Spacing Utilities (`_spacing.css`)

**File**: `frontend/css/design-system/_spacing.css`

```css
/**
 * Spacing Utilities
 * Margin, padding, and gap utilities using spacing tokens
 */

/* ============================================
   MARGIN UTILITIES
   ============================================ */

/* Margin All */
.m-0 { margin: var(--space-0); }
.m-1 { margin: var(--space-1); }
.m-2 { margin: var(--space-2); }
.m-3 { margin: var(--space-3); }
.m-4 { margin: var(--space-4); }
.m-5 { margin: var(--space-5); }
.m-6 { margin: var(--space-6); }
.m-8 { margin: var(--space-8); }
.m-10 { margin: var(--space-10); }
.m-12 { margin: var(--space-12); }
.m-auto { margin: auto; }

/* Margin X (horizontal) */
.mx-0 { margin-left: var(--space-0); margin-right: var(--space-0); }
.mx-1 { margin-left: var(--space-1); margin-right: var(--space-1); }
.mx-2 { margin-left: var(--space-2); margin-right: var(--space-2); }
.mx-3 { margin-left: var(--space-3); margin-right: var(--space-3); }
.mx-4 { margin-left: var(--space-4); margin-right: var(--space-4); }
.mx-6 { margin-left: var(--space-6); margin-right: var(--space-6); }
.mx-8 { margin-left: var(--space-8); margin-right: var(--space-8); }
.mx-auto { margin-left: auto; margin-right: auto; }

/* Margin Y (vertical) */
.my-0 { margin-top: var(--space-0); margin-bottom: var(--space-0); }
.my-1 { margin-top: var(--space-1); margin-bottom: var(--space-1); }
.my-2 { margin-top: var(--space-2); margin-bottom: var(--space-2); }
.my-3 { margin-top: var(--space-3); margin-bottom: var(--space-3); }
.my-4 { margin-top: var(--space-4); margin-bottom: var(--space-4); }
.my-6 { margin-top: var(--space-6); margin-bottom: var(--space-6); }
.my-8 { margin-top: var(--space-8); margin-bottom: var(--space-8); }

/* Margin Top */
.mt-0 { margin-top: var(--space-0); }
.mt-1 { margin-top: var(--space-1); }
.mt-2 { margin-top: var(--space-2); }
.mt-3 { margin-top: var(--space-3); }
.mt-4 { margin-top: var(--space-4); }
.mt-5 { margin-top: var(--space-5); }
.mt-6 { margin-top: var(--space-6); }
.mt-8 { margin-top: var(--space-8); }
.mt-10 { margin-top: var(--space-10); }
.mt-12 { margin-top: var(--space-12); }

/* Margin Bottom */
.mb-0 { margin-bottom: var(--space-0); }
.mb-1 { margin-bottom: var(--space-1); }
.mb-2 { margin-bottom: var(--space-2); }
.mb-3 { margin-bottom: var(--space-3); }
.mb-4 { margin-bottom: var(--space-4); }
.mb-5 { margin-bottom: var(--space-5); }
.mb-6 { margin-bottom: var(--space-6); }
.mb-8 { margin-bottom: var(--space-8); }
.mb-10 { margin-bottom: var(--space-10); }
.mb-12 { margin-bottom: var(--space-12); }

/* Margin Left */
.ml-0 { margin-left: var(--space-0); }
.ml-1 { margin-left: var(--space-1); }
.ml-2 { margin-left: var(--space-2); }
.ml-3 { margin-left: var(--space-3); }
.ml-4 { margin-left: var(--space-4); }
.ml-auto { margin-left: auto; }

/* Margin Right */
.mr-0 { margin-right: var(--space-0); }
.mr-1 { margin-right: var(--space-1); }
.mr-2 { margin-right: var(--space-2); }
.mr-3 { margin-right: var(--space-3); }
.mr-4 { margin-right: var(--space-4); }
.mr-auto { margin-right: auto; }

/* ============================================
   PADDING UTILITIES
   ============================================ */

/* Padding All */
.p-0 { padding: var(--space-0); }
.p-1 { padding: var(--space-1); }
.p-2 { padding: var(--space-2); }
.p-3 { padding: var(--space-3); }
.p-4 { padding: var(--space-4); }
.p-5 { padding: var(--space-5); }
.p-6 { padding: var(--space-6); }
.p-8 { padding: var(--space-8); }
.p-10 { padding: var(--space-10); }
.p-12 { padding: var(--space-12); }

/* Padding X (horizontal) */
.px-0 { padding-left: var(--space-0); padding-right: var(--space-0); }
.px-1 { padding-left: var(--space-1); padding-right: var(--space-1); }
.px-2 { padding-left: var(--space-2); padding-right: var(--space-2); }
.px-3 { padding-left: var(--space-3); padding-right: var(--space-3); }
.px-4 { padding-left: var(--space-4); padding-right: var(--space-4); }
.px-5 { padding-left: var(--space-5); padding-right: var(--space-5); }
.px-6 { padding-left: var(--space-6); padding-right: var(--space-6); }
.px-8 { padding-left: var(--space-8); padding-right: var(--space-8); }

/* Padding Y (vertical) */
.py-0 { padding-top: var(--space-0); padding-bottom: var(--space-0); }
.py-1 { padding-top: var(--space-1); padding-bottom: var(--space-1); }
.py-2 { padding-top: var(--space-2); padding-bottom: var(--space-2); }
.py-3 { padding-top: var(--space-3); padding-bottom: var(--space-3); }
.py-4 { padding-top: var(--space-4); padding-bottom: var(--space-4); }
.py-5 { padding-top: var(--space-5); padding-bottom: var(--space-5); }
.py-6 { padding-top: var(--space-6); padding-bottom: var(--space-6); }
.py-8 { padding-top: var(--space-8); padding-bottom: var(--space-8); }

/* Padding Individual Sides */
.pt-0 { padding-top: var(--space-0); }
.pt-2 { padding-top: var(--space-2); }
.pt-4 { padding-top: var(--space-4); }
.pt-6 { padding-top: var(--space-6); }
.pt-8 { padding-top: var(--space-8); }

.pb-0 { padding-bottom: var(--space-0); }
.pb-2 { padding-bottom: var(--space-2); }
.pb-4 { padding-bottom: var(--space-4); }
.pb-6 { padding-bottom: var(--space-6); }
.pb-8 { padding-bottom: var(--space-8); }

.pl-0 { padding-left: var(--space-0); }
.pl-2 { padding-left: var(--space-2); }
.pl-4 { padding-left: var(--space-4); }
.pl-6 { padding-left: var(--space-6); }

.pr-0 { padding-right: var(--space-0); }
.pr-2 { padding-right: var(--space-2); }
.pr-4 { padding-right: var(--space-4); }
.pr-6 { padding-right: var(--space-6); }

/* ============================================
   GAP UTILITIES (for Flexbox/Grid)
   ============================================ */
.gap-0 { gap: var(--space-0); }
.gap-1 { gap: var(--space-1); }
.gap-2 { gap: var(--space-2); }
.gap-3 { gap: var(--space-3); }
.gap-4 { gap: var(--space-4); }
.gap-5 { gap: var(--space-5); }
.gap-6 { gap: var(--space-6); }
.gap-8 { gap: var(--space-8); }
.gap-10 { gap: var(--space-10); }
.gap-12 { gap: var(--space-12); }

.gap-x-2 { column-gap: var(--space-2); }
.gap-x-4 { column-gap: var(--space-4); }
.gap-x-6 { column-gap: var(--space-6); }
.gap-x-8 { column-gap: var(--space-8); }

.gap-y-2 { row-gap: var(--space-2); }
.gap-y-4 { row-gap: var(--space-4); }
.gap-y-6 { row-gap: var(--space-6); }
.gap-y-8 { row-gap: var(--space-8); }

/* ============================================
   WIDTH/HEIGHT UTILITIES
   ============================================ */
.w-full { width: 100%; }
.w-screen { width: 100vw; }
.w-auto { width: auto; }
.w-fit { width: fit-content; }

.h-full { height: 100%; }
.h-screen { height: 100vh; }
.h-auto { height: auto; }
.h-fit { height: fit-content; }

.min-h-screen { min-height: 100vh; }
.max-w-screen-sm { max-width: var(--breakpoint-sm); }
.max-w-screen-md { max-width: var(--breakpoint-md); }
.max-w-screen-lg { max-width: var(--breakpoint-lg); }
.max-w-screen-xl { max-width: var(--breakpoint-xl); }
```

**Acceptance Criteria**:
- [ ] Margin utilities (m, mx, my, mt, mb, ml, mr)
- [ ] Padding utilities (p, px, py, pt, pb, pl, pr)
- [ ] Gap utilities for flexbox/grid
- [ ] Width/height utilities
- [ ] All use spacing tokens

---

### Task 5: Create Effects System (`_effects.css`)

**File**: `frontend/css/design-system/_effects.css`

```css
/**
 * Visual Effects
 * Shadows, blurs, gradients, glassmorphism, neumorphism
 */

/* ============================================
   SHADOW UTILITIES
   ============================================ */
.shadow-none { box-shadow: none; }
.shadow-xs { box-shadow: var(--shadow-xs); }
.shadow-sm { box-shadow: var(--shadow-sm); }
.shadow-md { box-shadow: var(--shadow-md); }
.shadow-lg { box-shadow: var(--shadow-lg); }
.shadow-xl { box-shadow: var(--shadow-xl); }
.shadow-2xl { box-shadow: var(--shadow-2xl); }
.shadow-inner { box-shadow: var(--shadow-inner); }

/* Dark mode shadows */
.shadow-dark-sm { box-shadow: var(--shadow-dark-sm); }
.shadow-dark-md { box-shadow: var(--shadow-dark-md); }
.shadow-dark-lg { box-shadow: var(--shadow-dark-lg); }
.shadow-dark-xl { box-shadow: var(--shadow-dark-xl); }

/* Glow shadows */
.shadow-glow-primary { box-shadow: var(--glow-primary); }
.shadow-glow-success { box-shadow: var(--glow-success); }
.shadow-glow-warning { box-shadow: var(--glow-warning); }
.shadow-glow-danger { box-shadow: var(--glow-danger); }

/* ============================================
   GLASSMORPHISM EFFECTS
   ============================================ */
.glass {
  background: var(--bg-glass);
  backdrop-filter: blur(12px) saturate(150%);
  -webkit-backdrop-filter: blur(12px) saturate(150%);
  border: 1px solid var(--bg-glass-border);
}

.glass-subtle {
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(8px) saturate(120%);
  -webkit-backdrop-filter: blur(8px) saturate(120%);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.glass-medium {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.glass-strong {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px) saturate(200%);
  -webkit-backdrop-filter: blur(20px) saturate(200%);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

/* Glassmorphism fallback for unsupported browsers */
@supports not (backdrop-filter: blur(10px)) {
  .glass,
  .glass-subtle,
  .glass-medium,
  .glass-strong {
    background: rgba(30, 30, 30, 0.95);
  }
}

/* ============================================
   NEUMORPHISM EFFECTS
   ============================================ */
.neumorphic {
  background: var(--bg-elevated);
  box-shadow:
    6px 6px 12px rgba(0, 0, 0, 0.4),
    -6px -6px 12px rgba(255, 255, 255, 0.05);
}

.neumorphic-inset {
  background: var(--bg-elevated);
  box-shadow:
    inset 4px 4px 8px rgba(0, 0, 0, 0.3),
    inset -4px -4px 8px rgba(255, 255, 255, 0.03);
}

.neumorphic-subtle {
  background: var(--bg-elevated);
  box-shadow:
    3px 3px 6px rgba(0, 0, 0, 0.3),
    -3px -3px 6px rgba(255, 255, 255, 0.03);
}

/* ============================================
   BLUR UTILITIES
   ============================================ */
.blur-none { filter: blur(0); }
.blur-sm { filter: blur(4px); }
.blur-md { filter: blur(8px); }
.blur-lg { filter: blur(16px); }
.blur-xl { filter: blur(24px); }
.blur-2xl { filter: blur(40px); }

.backdrop-blur-none { backdrop-filter: blur(0); }
.backdrop-blur-sm { backdrop-filter: blur(4px); }
.backdrop-blur-md { backdrop-filter: blur(8px); }
.backdrop-blur-lg { backdrop-filter: blur(16px); }
.backdrop-blur-xl { backdrop-filter: blur(24px); }

/* ============================================
   OPACITY UTILITIES
   ============================================ */
.opacity-0 { opacity: 0; }
.opacity-5 { opacity: 0.05; }
.opacity-10 { opacity: 0.1; }
.opacity-20 { opacity: 0.2; }
.opacity-25 { opacity: 0.25; }
.opacity-30 { opacity: 0.3; }
.opacity-40 { opacity: 0.4; }
.opacity-50 { opacity: 0.5; }
.opacity-60 { opacity: 0.6; }
.opacity-70 { opacity: 0.7; }
.opacity-75 { opacity: 0.75; }
.opacity-80 { opacity: 0.8; }
.opacity-90 { opacity: 0.9; }
.opacity-100 { opacity: 1; }

/* ============================================
   BORDER UTILITIES
   ============================================ */
.border { border: 1px solid var(--border-default); }
.border-0 { border: 0; }
.border-2 { border-width: 2px; }

.border-t { border-top: 1px solid var(--border-default); }
.border-b { border-bottom: 1px solid var(--border-default); }
.border-l { border-left: 1px solid var(--border-default); }
.border-r { border-right: 1px solid var(--border-default); }

.border-subtle { border-color: var(--border-subtle); }
.border-medium { border-color: var(--border-medium); }
.border-strong { border-color: var(--border-strong); }
.border-primary { border-color: var(--interactive-default); }
.border-success { border-color: var(--status-success); }
.border-warning { border-color: var(--status-warning); }
.border-danger { border-color: var(--status-danger); }

/* Border Radius */
.rounded-none { border-radius: var(--radius-none); }
.rounded-sm { border-radius: var(--radius-sm); }
.rounded { border-radius: var(--radius-md); }
.rounded-md { border-radius: var(--radius-md); }
.rounded-lg { border-radius: var(--radius-lg); }
.rounded-xl { border-radius: var(--radius-xl); }
.rounded-2xl { border-radius: var(--radius-2xl); }
.rounded-3xl { border-radius: var(--radius-3xl); }
.rounded-full { border-radius: var(--radius-full); }

/* ============================================
   GRADIENT BACKGROUNDS
   ============================================ */
.bg-gradient-primary { background: var(--gradient-primary); }
.bg-gradient-success { background: var(--gradient-success); }
.bg-gradient-warning { background: var(--gradient-warning); }
.bg-gradient-danger { background: var(--gradient-danger); }
.bg-gradient-surface { background: var(--gradient-surface); }

/* ============================================
   RING FOCUS INDICATOR
   ============================================ */
.ring-0 { box-shadow: 0 0 0 0 transparent; }
.ring-1 { box-shadow: 0 0 0 1px var(--border-focus); }
.ring-2 { box-shadow: 0 0 0 2px var(--border-focus); }
.ring-4 { box-shadow: 0 0 0 4px var(--border-focus); }

.ring-primary { --ring-color: var(--color-primary-500); }
.ring-success { --ring-color: var(--color-success-500); }
.ring-warning { --ring-color: var(--color-warning-500); }
.ring-danger { --ring-color: var(--color-danger-500); }

/* ============================================
   OVERFLOW UTILITIES
   ============================================ */
.overflow-auto { overflow: auto; }
.overflow-hidden { overflow: hidden; }
.overflow-visible { overflow: visible; }
.overflow-scroll { overflow: scroll; }
.overflow-x-auto { overflow-x: auto; }
.overflow-y-auto { overflow-y: auto; }
.overflow-x-hidden { overflow-x: hidden; }
.overflow-y-hidden { overflow-y: hidden; }
```

**Acceptance Criteria**:
- [ ] Shadow utilities (standard and dark mode)
- [ ] Glow effects
- [ ] Glassmorphism classes with browser fallback
- [ ] Neumorphism classes
- [ ] Blur utilities
- [ ] Opacity utilities
- [ ] Border utilities
- [ ] Gradient backgrounds
- [ ] Focus ring utilities

---

### Task 6: Create Modern CSS Reset (`_reset.css`)

**File**: `frontend/css/design-system/_reset.css`

```css
/**
 * Modern CSS Reset
 * Based on Josh Comeau's CSS Reset with additions
 */

/* Box sizing rules */
*,
*::before,
*::after {
  box-sizing: border-box;
}

/* Remove default margin and padding */
* {
  margin: 0;
  padding: 0;
}

/* Prevent font size inflation */
html {
  -moz-text-size-adjust: none;
  -webkit-text-size-adjust: none;
  text-size-adjust: none;
}

/* Remove list styles on ul, ol with role="list" */
ul[role='list'],
ol[role='list'] {
  list-style: none;
}

/* Set core body defaults */
body {
  min-height: 100vh;
  line-height: 1.5;
}

/* Set shorter line heights on headings and interactive elements */
h1, h2, h3, h4, h5, h6,
button, input, label {
  line-height: 1.1;
}

/* Balance text wrapping on headings */
h1, h2, h3, h4, h5, h6 {
  text-wrap: balance;
}

/* A elements that don't have a class get default styles */
a:not([class]) {
  text-decoration-skip-ink: auto;
  color: currentColor;
}

/* Make images easier to work with */
img,
picture,
video,
canvas,
svg {
  display: block;
  max-width: 100%;
}

/* Inherit fonts for inputs and buttons */
input,
button,
textarea,
select {
  font: inherit;
  color: inherit;
}

/* Remove default button styles */
button {
  background: none;
  border: none;
  cursor: pointer;
}

/* Make sure textareas without a rows attribute are not tiny */
textarea:not([rows]) {
  min-height: 10em;
}

/* Anything that has been anchored to should have extra scroll margin */
:target {
  scroll-margin-block: 5ex;
}

/* Remove all animations and transitions for people who prefer not to see them */
@media (prefers-reduced-motion: reduce) {
  html:focus-within {
    scroll-behavior: auto;
  }

  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* Remove default fieldset styles */
fieldset {
  border: none;
}

/* Remove default table spacing */
table {
  border-collapse: collapse;
  border-spacing: 0;
}

/* Improve link focus */
a:focus-visible,
button:focus-visible {
  outline: 2px solid var(--border-focus, currentColor);
  outline-offset: 2px;
}

/* Hide focus outline for mouse users */
:focus:not(:focus-visible) {
  outline: none;
}

/* Improve scrollbar in supported browsers */
* {
  scrollbar-width: thin;
  scrollbar-color: var(--color-gray-600, #525252) transparent;
}

*::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

*::-webkit-scrollbar-track {
  background: transparent;
}

*::-webkit-scrollbar-thumb {
  background-color: var(--color-gray-600, #525252);
  border-radius: 4px;
}

*::-webkit-scrollbar-thumb:hover {
  background-color: var(--color-gray-500, #737373);
}

/* Selection styling */
::selection {
  background-color: var(--color-primary-500, #3b82f6);
  color: white;
}
```

**Acceptance Criteria**:
- [ ] Modern box-sizing applied
- [ ] Default margins/padding removed
- [ ] Typography defaults set
- [ ] Image handling improved
- [ ] Form element normalization
- [ ] Focus styles defined
- [ ] Reduced motion support
- [ ] Scrollbar styling
- [ ] Selection styling

---

### Task 7: Create Main Design System Import File

**File**: `frontend/css/design-system.css`

```css
/**
 * Macro Confluence Hub - Design System v2.0
 *
 * Import order matters:
 * 1. Reset - Normalize browser defaults
 * 2. Tokens - Raw design values
 * 3. Colors - Semantic color mappings
 * 4. Typography - Font system
 * 5. Spacing - Layout utilities
 * 6. Effects - Visual effects
 */

@import url('./design-system/_reset.css');
@import url('./design-system/_tokens.css');
@import url('./design-system/_colors.css');
@import url('./design-system/_typography.css');
@import url('./design-system/_spacing.css');
@import url('./design-system/_effects.css');

/* ============================================
   LAYOUT UTILITIES
   ============================================ */

/* Display */
.hidden { display: none; }
.block { display: block; }
.inline-block { display: inline-block; }
.inline { display: inline; }
.flex { display: flex; }
.inline-flex { display: inline-flex; }
.grid { display: grid; }

/* Flexbox */
.flex-row { flex-direction: row; }
.flex-col { flex-direction: column; }
.flex-wrap { flex-wrap: wrap; }
.flex-nowrap { flex-wrap: nowrap; }
.flex-1 { flex: 1 1 0%; }
.flex-auto { flex: 1 1 auto; }
.flex-none { flex: none; }
.grow { flex-grow: 1; }
.grow-0 { flex-grow: 0; }
.shrink { flex-shrink: 1; }
.shrink-0 { flex-shrink: 0; }

/* Alignment */
.items-start { align-items: flex-start; }
.items-center { align-items: center; }
.items-end { align-items: flex-end; }
.items-baseline { align-items: baseline; }
.items-stretch { align-items: stretch; }

.justify-start { justify-content: flex-start; }
.justify-center { justify-content: center; }
.justify-end { justify-content: flex-end; }
.justify-between { justify-content: space-between; }
.justify-around { justify-content: space-around; }
.justify-evenly { justify-content: space-evenly; }

.self-auto { align-self: auto; }
.self-start { align-self: flex-start; }
.self-center { align-self: center; }
.self-end { align-self: flex-end; }
.self-stretch { align-self: stretch; }

/* Positioning */
.relative { position: relative; }
.absolute { position: absolute; }
.fixed { position: fixed; }
.sticky { position: sticky; }

.inset-0 { inset: 0; }
.top-0 { top: 0; }
.right-0 { right: 0; }
.bottom-0 { bottom: 0; }
.left-0 { left: 0; }

/* Z-Index */
.z-0 { z-index: var(--z-0); }
.z-10 { z-index: var(--z-10); }
.z-20 { z-index: var(--z-20); }
.z-30 { z-index: var(--z-30); }
.z-40 { z-index: var(--z-40); }
.z-50 { z-index: var(--z-50); }
.z-dropdown { z-index: var(--z-dropdown); }
.z-sticky { z-index: var(--z-sticky); }
.z-fixed { z-index: var(--z-fixed); }
.z-modal { z-index: var(--z-modal); }
.z-tooltip { z-index: var(--z-tooltip); }
.z-toast { z-index: var(--z-toast); }

/* ============================================
   TRANSITION UTILITIES
   ============================================ */
.transition-none { transition: none; }
.transition-all { transition: all var(--duration-200) var(--ease-in-out); }
.transition-colors { transition: color, background-color, border-color var(--duration-200) var(--ease-in-out); }
.transition-opacity { transition: opacity var(--duration-200) var(--ease-in-out); }
.transition-transform { transition: transform var(--duration-200) var(--ease-in-out); }
.transition-shadow { transition: box-shadow var(--duration-200) var(--ease-in-out); }

.duration-75 { transition-duration: var(--duration-75); }
.duration-100 { transition-duration: var(--duration-100); }
.duration-150 { transition-duration: var(--duration-150); }
.duration-200 { transition-duration: var(--duration-200); }
.duration-300 { transition-duration: var(--duration-300); }
.duration-500 { transition-duration: var(--duration-500); }

.ease-linear { transition-timing-function: var(--ease-linear); }
.ease-in { transition-timing-function: var(--ease-in); }
.ease-out { transition-timing-function: var(--ease-out); }
.ease-in-out { transition-timing-function: var(--ease-in-out); }
.ease-bounce { transition-timing-function: var(--ease-bounce); }

/* ============================================
   TRANSFORM UTILITIES
   ============================================ */
.scale-90 { transform: scale(0.9); }
.scale-95 { transform: scale(0.95); }
.scale-100 { transform: scale(1); }
.scale-105 { transform: scale(1.05); }
.scale-110 { transform: scale(1.1); }

.rotate-0 { transform: rotate(0deg); }
.rotate-45 { transform: rotate(45deg); }
.rotate-90 { transform: rotate(90deg); }
.rotate-180 { transform: rotate(180deg); }

.translate-y-0 { transform: translateY(0); }
.translate-y-1 { transform: translateY(var(--space-1)); }
.translate-y-2 { transform: translateY(var(--space-2)); }
.-translate-y-1 { transform: translateY(calc(var(--space-1) * -1)); }
.-translate-y-2 { transform: translateY(calc(var(--space-2) * -1)); }

/* ============================================
   CURSOR UTILITIES
   ============================================ */
.cursor-auto { cursor: auto; }
.cursor-default { cursor: default; }
.cursor-pointer { cursor: pointer; }
.cursor-wait { cursor: wait; }
.cursor-text { cursor: text; }
.cursor-move { cursor: move; }
.cursor-not-allowed { cursor: not-allowed; }

/* ============================================
   USER SELECT
   ============================================ */
.select-none { user-select: none; }
.select-text { user-select: text; }
.select-all { user-select: all; }
.select-auto { user-select: auto; }

/* ============================================
   POINTER EVENTS
   ============================================ */
.pointer-events-none { pointer-events: none; }
.pointer-events-auto { pointer-events: auto; }

/* ============================================
   VISIBILITY
   ============================================ */
.visible { visibility: visible; }
.invisible { visibility: hidden; }

/* ============================================
   SCREEN READER ONLY
   ============================================ */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.not-sr-only {
  position: static;
  width: auto;
  height: auto;
  padding: 0;
  margin: 0;
  overflow: visible;
  clip: auto;
  white-space: normal;
}
```

**Acceptance Criteria**:
- [ ] All design system files imported in correct order
- [ ] Layout utilities defined
- [ ] Transition utilities defined
- [ ] Transform utilities defined
- [ ] Interaction utilities (cursor, select, pointer-events)
- [ ] Accessibility utilities (sr-only)

---

### Task 8: Update Existing style.css to Use Design System

**File**: `frontend/css/style.css` (Modifications)

Update the existing style.css to import and use the design system:

```css
/**
 * Macro Confluence Hub - Main Styles
 * Now using design system tokens
 */

/* Import Design System */
@import url('./design-system.css');

/* ============================================
   APPLICATION SHELL
   ============================================ */
body {
  background: var(--bg-base);
  color: var(--text-primary);
  min-height: 100vh;
}

.app-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--space-6);
}

/* ... rest of existing styles updated to use tokens ... */
```

**Acceptance Criteria**:
- [ ] Design system imported at top
- [ ] All hardcoded colors replaced with tokens
- [ ] All hardcoded spacing replaced with tokens
- [ ] All hardcoded typography replaced with tokens
- [ ] All hardcoded shadows/effects replaced with tokens

---

## Testing Checklist

- [ ] All CSS files parse without errors
- [ ] Design tokens render correctly in browser
- [ ] Dark theme displays properly
- [ ] Glassmorphism renders (with fallback for unsupported browsers)
- [ ] Typography hierarchy is visually clear
- [ ] Spacing is consistent throughout
- [ ] No visual regressions from current design

---

## Dependencies

**Required Font Files**:
- Inter (Google Fonts)
- JetBrains Mono (Google Fonts)

**Browser Support**:
- Chrome 80+
- Firefox 75+
- Safari 14+
- Edge 80+

**Polyfills/Fallbacks**:
- backdrop-filter fallback for older browsers

---

## Success Metrics

| Metric | Target |
|--------|--------|
| CSS file size (gzipped) | < 30KB total |
| Number of unique colors | < 50 |
| Number of font weights | < 6 |
| Design token coverage | 100% |

---

*Created: December 2025*
*Author: Claude Code Assistant*
