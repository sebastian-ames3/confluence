# PRD-028: Component Library Redesign

## Overview

Create a comprehensive library of reusable UI components with modern styling including glassmorphism, neumorphism, and micro-interactions. This library provides the building blocks for the entire dashboard interface.

**Status**: Proposed
**Priority**: High
**Depends On**: PRD-027 (Design System Foundation)
**Blocks**: PRD-029, PRD-030

---

## Goals

1. Create consistent, reusable component library
2. Implement glassmorphism and neumorphism variants
3. Build accessible, interactive components
4. Establish component API patterns
5. Enable rapid UI development

---

## File Structure

```
frontend/
├── css/
│   ├── components/
│   │   ├── _buttons.css
│   │   ├── _cards.css
│   │   ├── _badges.css
│   │   ├── _inputs.css
│   │   ├── _tabs.css
│   │   ├── _tables.css
│   │   ├── _tooltips.css
│   │   ├── _modals.css
│   │   ├── _toasts.css
│   │   ├── _progress.css
│   │   ├── _avatars.css
│   │   └── _loaders.css
│   └── components.css
├── js/
│   └── components/
│       ├── ripple.js
│       ├── tooltip.js
│       ├── modal.js
│       └── toast.js
```

---

## Implementation Tasks

### Task 1: Button Components (`_buttons.css`)

**File**: `frontend/css/components/_buttons.css`

```css
/**
 * Button Components
 * Variants: Primary, Secondary, Ghost, Danger, Success
 * Sizes: sm, md, lg
 * States: default, hover, active, disabled, loading
 */

/* ============================================
   BASE BUTTON
   ============================================ */
.btn {
  /* Layout */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);

  /* Sizing */
  padding: var(--space-2-5) var(--space-4);
  min-height: 40px;

  /* Typography */
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  line-height: 1;
  text-decoration: none;
  white-space: nowrap;

  /* Appearance */
  border: 1px solid transparent;
  border-radius: var(--radius-lg);
  cursor: pointer;

  /* Transitions */
  transition:
    background-color var(--duration-150) var(--ease-in-out),
    border-color var(--duration-150) var(--ease-in-out),
    color var(--duration-150) var(--ease-in-out),
    box-shadow var(--duration-150) var(--ease-in-out),
    transform var(--duration-150) var(--ease-in-out);

  /* Interaction */
  user-select: none;
  position: relative;
  overflow: hidden;
}

.btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px var(--bg-base), 0 0 0 4px var(--interactive-default);
}

.btn:disabled,
.btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

/* ============================================
   PRIMARY BUTTON
   ============================================ */
.btn-primary {
  background: var(--gradient-primary);
  color: var(--color-white);
  border-color: transparent;
  box-shadow: 0 4px 14px rgba(59, 130, 246, 0.3);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.btn-primary:active {
  transform: translateY(0);
  box-shadow: 0 2px 10px rgba(59, 130, 246, 0.3);
}

/* ============================================
   SECONDARY BUTTON
   ============================================ */
.btn-secondary {
  background: var(--bg-glass);
  color: var(--text-primary);
  border-color: var(--border-medium);
  backdrop-filter: blur(8px);
}

.btn-secondary:hover {
  background: var(--bg-glass-hover);
  border-color: var(--border-strong);
}

.btn-secondary:active {
  background: var(--bg-glass-active);
}

/* ============================================
   GHOST BUTTON
   ============================================ */
.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border-color: transparent;
}

.btn-ghost:hover {
  background: var(--bg-glass);
  color: var(--text-primary);
}

.btn-ghost:active {
  background: var(--bg-glass-active);
}

/* ============================================
   DANGER BUTTON
   ============================================ */
.btn-danger {
  background: var(--gradient-danger);
  color: var(--color-white);
  border-color: transparent;
  box-shadow: 0 4px 14px rgba(239, 68, 68, 0.3);
}

.btn-danger:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
}

.btn-danger:active {
  transform: translateY(0);
}

/* ============================================
   SUCCESS BUTTON
   ============================================ */
.btn-success {
  background: var(--gradient-success);
  color: var(--color-white);
  border-color: transparent;
  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
}

.btn-success:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

.btn-success:active {
  transform: translateY(0);
}

/* ============================================
   WARNING BUTTON
   ============================================ */
.btn-warning {
  background: var(--gradient-warning);
  color: var(--color-gray-900);
  border-color: transparent;
  box-shadow: 0 4px 14px rgba(245, 158, 11, 0.3);
}

.btn-warning:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(245, 158, 11, 0.4);
}

/* ============================================
   NEUMORPHIC BUTTON
   ============================================ */
.btn-neumorphic {
  background: var(--bg-elevated);
  color: var(--text-primary);
  border: none;
  box-shadow:
    6px 6px 12px rgba(0, 0, 0, 0.4),
    -6px -6px 12px rgba(255, 255, 255, 0.05);
}

.btn-neumorphic:hover {
  box-shadow:
    4px 4px 8px rgba(0, 0, 0, 0.4),
    -4px -4px 8px rgba(255, 255, 255, 0.05);
}

.btn-neumorphic:active {
  box-shadow:
    inset 4px 4px 8px rgba(0, 0, 0, 0.4),
    inset -4px -4px 8px rgba(255, 255, 255, 0.03);
}

/* ============================================
   BUTTON SIZES
   ============================================ */
.btn-sm {
  padding: var(--space-1-5) var(--space-3);
  min-height: 32px;
  font-size: var(--text-xs);
  border-radius: var(--radius-md);
}

.btn-lg {
  padding: var(--space-3-5) var(--space-6);
  min-height: 48px;
  font-size: var(--text-base);
  border-radius: var(--radius-xl);
}

.btn-xl {
  padding: var(--space-4) var(--space-8);
  min-height: 56px;
  font-size: var(--text-lg);
  border-radius: var(--radius-xl);
}

/* ============================================
   ICON BUTTONS
   ============================================ */
.btn-icon {
  padding: var(--space-2);
  min-height: 40px;
  min-width: 40px;
}

.btn-icon.btn-sm {
  padding: var(--space-1-5);
  min-height: 32px;
  min-width: 32px;
}

.btn-icon.btn-lg {
  padding: var(--space-3);
  min-height: 48px;
  min-width: 48px;
}

/* ============================================
   BUTTON WITH ICON
   ============================================ */
.btn svg,
.btn .icon {
  width: 1em;
  height: 1em;
  flex-shrink: 0;
}

.btn-icon-left svg,
.btn-icon-left .icon {
  margin-right: var(--space-1);
}

.btn-icon-right svg,
.btn-icon-right .icon {
  margin-left: var(--space-1);
}

/* ============================================
   LOADING STATE
   ============================================ */
.btn.loading {
  color: transparent;
  pointer-events: none;
}

.btn.loading::after {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: btn-spinner 0.6s linear infinite;
}

.btn-primary.loading::after,
.btn-danger.loading::after,
.btn-success.loading::after {
  border-color: rgba(255, 255, 255, 0.3);
  border-right-color: white;
}

@keyframes btn-spinner {
  to { transform: rotate(360deg); }
}

/* ============================================
   RIPPLE EFFECT (requires JS)
   ============================================ */
.btn .ripple {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.4);
  transform: scale(0);
  animation: ripple-effect 0.6s linear;
  pointer-events: none;
}

@keyframes ripple-effect {
  to {
    transform: scale(4);
    opacity: 0;
  }
}

/* ============================================
   BUTTON GROUP
   ============================================ */
.btn-group {
  display: inline-flex;
}

.btn-group .btn {
  border-radius: 0;
}

.btn-group .btn:first-child {
  border-radius: var(--radius-lg) 0 0 var(--radius-lg);
}

.btn-group .btn:last-child {
  border-radius: 0 var(--radius-lg) var(--radius-lg) 0;
}

.btn-group .btn:not(:last-child) {
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-group .btn:hover {
  z-index: 1;
}
```

**Acceptance Criteria**:
- [ ] Base button with consistent styling
- [ ] Primary, secondary, ghost, danger, success variants
- [ ] Neumorphic variant
- [ ] Size variants (sm, md, lg, xl)
- [ ] Icon button support
- [ ] Loading state
- [ ] Ripple effect placeholder
- [ ] Button groups
- [ ] Focus states (accessibility)
- [ ] Disabled states

---

### Task 2: Card Components (`_cards.css`)

**File**: `frontend/css/components/_cards.css`

```css
/**
 * Card Components
 * Variants: Default, Glass, Elevated, Interactive
 */

/* ============================================
   BASE CARD
   ============================================ */
.card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-2xl);
  padding: var(--space-6);
  transition: all var(--duration-200) var(--ease-in-out);
}

/* ============================================
   GLASS CARD
   ============================================ */
.card-glass {
  background: var(--bg-glass);
  backdrop-filter: blur(12px) saturate(150%);
  -webkit-backdrop-filter: blur(12px) saturate(150%);
  border: 1px solid var(--bg-glass-border);
  border-radius: var(--radius-2xl);
  padding: var(--space-6);
  transition: all var(--duration-200) var(--ease-in-out);
}

.card-glass:hover {
  background: var(--bg-glass-hover);
  border-color: var(--border-medium);
}

/* ============================================
   ELEVATED CARD
   ============================================ */
.card-elevated {
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-2xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-dark-md);
  transition: all var(--duration-200) var(--ease-in-out);
}

.card-elevated:hover {
  box-shadow: var(--shadow-dark-lg);
  transform: translateY(-2px);
}

/* ============================================
   INTERACTIVE CARD
   ============================================ */
.card-interactive {
  background: var(--bg-glass);
  backdrop-filter: blur(12px) saturate(150%);
  -webkit-backdrop-filter: blur(12px) saturate(150%);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-2xl);
  padding: var(--space-6);
  cursor: pointer;
  transition: all var(--duration-200) var(--ease-in-out);
}

.card-interactive:hover {
  background: var(--bg-glass-hover);
  border-color: var(--interactive-default);
  transform: translateY(-4px);
  box-shadow: var(--shadow-dark-lg), var(--glow-primary);
}

.card-interactive:active {
  transform: translateY(-2px);
}

/* ============================================
   NEUMORPHIC CARD
   ============================================ */
.card-neumorphic {
  background: var(--bg-elevated);
  border: none;
  border-radius: var(--radius-2xl);
  padding: var(--space-6);
  box-shadow:
    8px 8px 16px rgba(0, 0, 0, 0.4),
    -8px -8px 16px rgba(255, 255, 255, 0.05);
  transition: all var(--duration-200) var(--ease-in-out);
}

.card-neumorphic:hover {
  box-shadow:
    6px 6px 12px rgba(0, 0, 0, 0.4),
    -6px -6px 12px rgba(255, 255, 255, 0.05);
}

/* ============================================
   CARD WITH ACCENT BORDER
   ============================================ */
.card-accent {
  position: relative;
  overflow: hidden;
}

.card-accent::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--gradient-primary);
}

.card-accent-left::before {
  top: 0;
  left: 0;
  bottom: 0;
  right: auto;
  width: 3px;
  height: auto;
}

.card-accent-success::before {
  background: var(--gradient-success);
}

.card-accent-warning::before {
  background: var(--gradient-warning);
}

.card-accent-danger::before {
  background: var(--gradient-danger);
}

/* ============================================
   CARD HEADER
   ============================================ */
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border-subtle);
}

.card-header-simple {
  margin-bottom: var(--space-4);
}

.card-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  line-height: var(--leading-tight);
}

.card-subtitle {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-top: var(--space-1);
}

.card-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-lg);
  background: var(--gradient-primary);
  color: white;
  flex-shrink: 0;
}

/* ============================================
   CARD BODY
   ============================================ */
.card-body {
  color: var(--text-primary);
}

/* ============================================
   CARD FOOTER
   ============================================ */
.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border-subtle);
}

/* ============================================
   CARD SIZES
   ============================================ */
.card-sm {
  padding: var(--space-4);
  border-radius: var(--radius-xl);
}

.card-lg {
  padding: var(--space-8);
  border-radius: var(--radius-3xl);
}

/* ============================================
   KPI CARD
   ============================================ */
.kpi-card {
  background: var(--bg-glass);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-2xl);
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  transition: all var(--duration-200) var(--ease-in-out);
}

.kpi-card:hover {
  background: var(--bg-glass-hover);
  border-color: var(--border-medium);
  transform: translateY(-2px);
}

.kpi-label {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  color: var(--text-muted);
}

.kpi-value {
  font-family: var(--font-mono);
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  line-height: 1;
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
}

.kpi-trend {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-full);
}

.kpi-trend-up {
  background: var(--status-success-bg);
  color: var(--status-success);
}

.kpi-trend-down {
  background: var(--status-danger-bg);
  color: var(--status-danger);
}

.kpi-trend-neutral {
  background: var(--bg-glass);
  color: var(--text-muted);
}

.kpi-meta {
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-top: auto;
}

.kpi-sparkline {
  height: 40px;
  margin-top: var(--space-2);
}

/* ============================================
   SOURCE CARD
   ============================================ */
.source-card {
  background: var(--bg-glass);
  backdrop-filter: blur(8px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: var(--space-4);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  transition: all var(--duration-200) var(--ease-in-out);
}

.source-card:hover {
  background: var(--bg-glass-hover);
  border-color: var(--border-medium);
}

.source-card-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-lg);
  flex-shrink: 0;
}

.source-card-icon.youtube {
  background: var(--source-youtube-bg);
  color: var(--source-youtube);
}

.source-card-icon.discord {
  background: var(--source-discord-bg);
  color: var(--source-discord);
}

.source-card-icon.substack {
  background: var(--source-substack-bg);
  color: var(--source-substack);
}

.source-card-icon.macro42 {
  background: var(--source-42macro-bg);
  color: var(--source-42macro);
}

.source-card-icon.kt-technical {
  background: var(--source-kt-technical-bg);
  color: var(--source-kt-technical);
}

.source-card-content {
  flex: 1;
  min-width: 0;
}

.source-card-name {
  font-weight: var(--font-medium);
  color: var(--text-primary);
  font-size: var(--text-sm);
}

.source-card-stats {
  display: flex;
  gap: var(--space-3);
  font-size: var(--text-xs);
  color: var(--text-muted);
  margin-top: var(--space-1);
}

.source-card-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--status-success);
  flex-shrink: 0;
}

.source-card-status.stale {
  background: var(--status-warning);
}

.source-card-status.error {
  background: var(--status-danger);
}

/* ============================================
   THEME CARD
   ============================================ */
.theme-card {
  background: var(--bg-glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-2xl);
  padding: var(--space-5);
  cursor: pointer;
  transition: all var(--duration-200) var(--ease-in-out);
}

.theme-card:hover {
  background: var(--bg-glass-hover);
  border-color: var(--interactive-default);
  transform: translateY(-2px);
  box-shadow: var(--glow-primary);
}

.theme-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.theme-card-title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  line-height: var(--leading-snug);
}

.theme-card-status {
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-full);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.theme-card-status.emerging {
  background: var(--status-info-bg);
  color: var(--status-info);
}

.theme-card-status.active {
  background: var(--status-success-bg);
  color: var(--status-success);
}

.theme-card-status.evolved {
  background: rgba(139, 92, 246, 0.1);
  color: var(--color-purple-400);
}

.theme-card-status.dormant {
  background: var(--bg-glass);
  color: var(--text-muted);
}

.theme-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-3);
}

.theme-card-conviction {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.theme-card-sources {
  display: flex;
  gap: var(--space-1);
}
```

**Acceptance Criteria**:
- [ ] Base card component
- [ ] Glass card variant
- [ ] Elevated card variant
- [ ] Interactive card variant
- [ ] Neumorphic card variant
- [ ] Accent border variants
- [ ] Card header, body, footer sections
- [ ] KPI card component
- [ ] Source card component
- [ ] Theme card component
- [ ] Size variants

---

### Task 3: Badge Components (`_badges.css`)

**File**: `frontend/css/components/_badges.css`

```css
/**
 * Badge & Tag Components
 * Status indicators, labels, and tags
 */

/* ============================================
   BASE BADGE
   ============================================ */
.badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  line-height: 1;
  border-radius: var(--radius-md);
  white-space: nowrap;
}

/* ============================================
   BADGE VARIANTS
   ============================================ */
.badge-default {
  background: var(--bg-glass);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
}

.badge-primary {
  background: var(--status-info-bg);
  color: var(--status-info);
  border: 1px solid var(--status-info-border);
}

.badge-success {
  background: var(--status-success-bg);
  color: var(--status-success);
  border: 1px solid var(--status-success-border);
}

.badge-warning {
  background: var(--status-warning-bg);
  color: var(--status-warning);
  border: 1px solid var(--status-warning-border);
}

.badge-danger {
  background: var(--status-danger-bg);
  color: var(--status-danger);
  border: 1px solid var(--status-danger-border);
}

/* ============================================
   SENTIMENT BADGES
   ============================================ */
.badge-bullish {
  background: var(--sentiment-bullish-bg);
  color: var(--sentiment-bullish);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.badge-bearish {
  background: var(--sentiment-bearish-bg);
  color: var(--sentiment-bearish);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.badge-neutral {
  background: var(--sentiment-neutral-bg);
  color: var(--sentiment-neutral);
  border: 1px solid rgba(163, 163, 163, 0.3);
}

/* ============================================
   SOURCE BADGES
   ============================================ */
.badge-youtube {
  background: var(--source-youtube-bg);
  color: var(--source-youtube);
  border: 1px solid rgba(255, 0, 0, 0.3);
}

.badge-discord {
  background: var(--source-discord-bg);
  color: var(--source-discord);
  border: 1px solid rgba(88, 101, 242, 0.3);
}

.badge-substack {
  background: var(--source-substack-bg);
  color: var(--source-substack);
  border: 1px solid rgba(255, 103, 25, 0.3);
}

.badge-42macro {
  background: var(--source-42macro-bg);
  color: var(--source-42macro);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.badge-kt-technical {
  background: var(--source-kt-technical-bg);
  color: var(--source-kt-technical);
  border: 1px solid rgba(234, 179, 8, 0.3);
}

/* ============================================
   BADGE WITH DOT
   ============================================ */
.badge-dot::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

/* Animated dot */
.badge-dot-pulse::before {
  animation: badge-pulse 2s ease-in-out infinite;
}

@keyframes badge-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* ============================================
   PILL BADGES (Fully Rounded)
   ============================================ */
.badge-pill {
  border-radius: var(--radius-full);
  padding: var(--space-1) var(--space-3);
}

/* ============================================
   BADGE SIZES
   ============================================ */
.badge-sm {
  padding: var(--space-0-5) var(--space-1-5);
  font-size: 10px;
}

.badge-lg {
  padding: var(--space-1-5) var(--space-3);
  font-size: var(--text-sm);
}

/* ============================================
   THEME TAGS (Interactive)
   ============================================ */
.tag {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1-5);
  padding: var(--space-1-5) var(--space-3);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-primary-300);
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all var(--duration-200) var(--ease-in-out);
}

.tag:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: var(--color-primary-500);
  box-shadow: var(--glow-primary);
  transform: scale(1.05);
}

.tag::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: tag-pulse 2s ease-in-out infinite;
}

@keyframes tag-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(0.9); }
}

/* ============================================
   CONVICTION BADGES
   ============================================ */
.conviction-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-2);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  border-radius: var(--radius-full);
}

.conviction-badge-high {
  background: var(--status-success-bg);
  color: var(--status-success);
}

.conviction-badge-medium {
  background: var(--status-warning-bg);
  color: var(--status-warning);
}

.conviction-badge-low {
  background: var(--status-danger-bg);
  color: var(--status-danger);
}

.conviction-badge-table-pounding {
  background: var(--status-info-bg);
  color: var(--status-info);
}

/* ============================================
   MARKET REGIME BADGE
   ============================================ */
.regime-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-xs);
  font-weight: var(--font-bold);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wider);
  border-radius: var(--radius-full);
  transition: all var(--duration-300) var(--ease-in-out);
}

.regime-badge-risk-on {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(34, 197, 94, 0.1));
  color: var(--color-success-400);
  border: 1px solid rgba(16, 185, 129, 0.4);
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.2);
}

.regime-badge-risk-off {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.1));
  color: var(--color-danger-400);
  border: 1px solid rgba(239, 68, 68, 0.4);
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
}

.regime-badge-transitioning {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(217, 119, 6, 0.1));
  color: var(--color-warning-400);
  border: 1px solid rgba(245, 158, 11, 0.4);
  animation: regime-pulse 2s ease-in-out infinite;
}

@keyframes regime-pulse {
  0%, 100% { box-shadow: 0 0 20px rgba(245, 158, 11, 0.2); }
  50% { box-shadow: 0 0 30px rgba(245, 158, 11, 0.4); }
}

.regime-badge-range-bound {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(124, 58, 237, 0.1));
  color: var(--color-purple-400);
  border: 1px solid rgba(139, 92, 246, 0.4);
}

.regime-badge-unclear {
  background: var(--bg-glass);
  color: var(--text-muted);
  border: 1px solid var(--border-subtle);
}

/* ============================================
   LIVE INDICATOR
   ============================================ */
.live-indicator {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  color: var(--text-muted);
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--status-success);
  position: relative;
}

.live-dot::before {
  content: '';
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  border: 2px solid var(--status-success);
  animation: live-ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
}

@keyframes live-ping {
  75%, 100% {
    transform: scale(2);
    opacity: 0;
  }
}

.live-dot.disconnected {
  background: var(--status-danger);
}

.live-dot.disconnected::before {
  animation: none;
  display: none;
}
```

**Acceptance Criteria**:
- [ ] Base badge component
- [ ] Status variant badges (primary, success, warning, danger)
- [ ] Sentiment badges (bullish, bearish, neutral)
- [ ] Source brand badges
- [ ] Badge with dot indicator
- [ ] Pill (fully rounded) badges
- [ ] Size variants
- [ ] Interactive theme tags
- [ ] Conviction badges
- [ ] Market regime badges
- [ ] Live indicator

---

### Task 4: Input Components (`_inputs.css`)

**File**: `frontend/css/components/_inputs.css`

```css
/**
 * Form Input Components
 * Text inputs, selects, checkboxes, etc.
 */

/* ============================================
   BASE INPUT
   ============================================ */
.input {
  width: 100%;
  padding: var(--space-2-5) var(--space-4);
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  color: var(--text-primary);
  background: var(--bg-glass);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-lg);
  transition: all var(--duration-200) var(--ease-in-out);
}

.input::placeholder {
  color: var(--text-muted);
}

.input:hover {
  border-color: var(--border-strong);
}

.input:focus {
  outline: none;
  border-color: var(--interactive-default);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--bg-surface);
}

/* ============================================
   INPUT WITH ICON
   ============================================ */
.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  pointer-events: none;
}

.input-icon-left {
  left: var(--space-3);
}

.input-icon-right {
  right: var(--space-3);
}

.input-with-icon-left {
  padding-left: var(--space-10);
}

.input-with-icon-right {
  padding-right: var(--space-10);
}

/* ============================================
   SEARCH INPUT
   ============================================ */
.search-input {
  background: var(--bg-glass);
  backdrop-filter: blur(8px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  padding: var(--space-3) var(--space-5);
  padding-left: var(--space-12);
}

.search-input:focus {
  background: var(--bg-glass-hover);
  border-color: var(--interactive-default);
}

/* ============================================
   SELECT
   ============================================ */
.select {
  appearance: none;
  width: 100%;
  padding: var(--space-2-5) var(--space-4);
  padding-right: var(--space-10);
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  color: var(--text-primary);
  background: var(--bg-glass);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-200) var(--ease-in-out);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23a0a0a0' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right var(--space-3) center;
}

.select:hover {
  border-color: var(--border-strong);
}

.select:focus {
  outline: none;
  border-color: var(--interactive-default);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* ============================================
   TEXTAREA
   ============================================ */
.textarea {
  width: 100%;
  min-height: 100px;
  padding: var(--space-3) var(--space-4);
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  color: var(--text-primary);
  background: var(--bg-glass);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-lg);
  resize: vertical;
  transition: all var(--duration-200) var(--ease-in-out);
}

.textarea:focus {
  outline: none;
  border-color: var(--interactive-default);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* ============================================
   CHECKBOX
   ============================================ */
.checkbox {
  appearance: none;
  width: 18px;
  height: 18px;
  border: 2px solid var(--border-medium);
  border-radius: var(--radius-sm);
  background: var(--bg-glass);
  cursor: pointer;
  transition: all var(--duration-150) var(--ease-in-out);
  position: relative;
}

.checkbox:hover {
  border-color: var(--interactive-default);
}

.checkbox:checked {
  background: var(--interactive-default);
  border-color: var(--interactive-default);
}

.checkbox:checked::after {
  content: '';
  position: absolute;
  left: 5px;
  top: 2px;
  width: 4px;
  height: 8px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.checkbox:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

/* ============================================
   TOGGLE SWITCH
   ============================================ */
.toggle {
  position: relative;
  width: 44px;
  height: 24px;
  background: var(--bg-elevated);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: background var(--duration-200) var(--ease-in-out);
}

.toggle::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: var(--text-secondary);
  border-radius: 50%;
  transition: all var(--duration-200) var(--ease-bounce);
  box-shadow: var(--shadow-sm);
}

.toggle.active {
  background: var(--interactive-default);
}

.toggle.active::after {
  transform: translateX(20px);
  background: white;
}

/* ============================================
   FORM GROUPS
   ============================================ */
.form-group {
  margin-bottom: var(--space-4);
}

.form-label {
  display: block;
  margin-bottom: var(--space-2);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
}

.form-hint {
  margin-top: var(--space-1);
  font-size: var(--text-xs);
  color: var(--text-muted);
}

.form-error {
  margin-top: var(--space-1);
  font-size: var(--text-xs);
  color: var(--status-danger);
}

/* ============================================
   INPUT STATES
   ============================================ */
.input-error {
  border-color: var(--status-danger);
}

.input-error:focus {
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.input-success {
  border-color: var(--status-success);
}

.input-success:focus {
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

/* ============================================
   INPUT SIZES
   ============================================ */
.input-sm {
  padding: var(--space-1-5) var(--space-3);
  font-size: var(--text-xs);
}

.input-lg {
  padding: var(--space-3-5) var(--space-5);
  font-size: var(--text-base);
}
```

**Acceptance Criteria**:
- [ ] Base text input
- [ ] Input with icon (left/right)
- [ ] Search input variant
- [ ] Select dropdown
- [ ] Textarea
- [ ] Checkbox
- [ ] Toggle switch
- [ ] Form groups with labels
- [ ] Error/success states
- [ ] Size variants

---

### Task 5: Create Component Import File

**File**: `frontend/css/components.css`

```css
/**
 * Component Library
 * Import all component styles
 */

@import url('./components/_buttons.css');
@import url('./components/_cards.css');
@import url('./components/_badges.css');
@import url('./components/_inputs.css');
@import url('./components/_tabs.css');
@import url('./components/_tables.css');
@import url('./components/_tooltips.css');
@import url('./components/_modals.css');
@import url('./components/_toasts.css');
@import url('./components/_progress.css');
@import url('./components/_loaders.css');
```

---

### Task 6: Tab Components (`_tabs.css`)

**File**: `frontend/css/components/_tabs.css`

```css
/**
 * Tab Components
 * Navigation tabs and tab panels
 */

/* ============================================
   TAB LIST
   ============================================ */
.tabs {
  display: flex;
  gap: var(--space-1);
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: var(--space-6);
}

.tabs-pills {
  border-bottom: none;
  background: var(--bg-glass);
  padding: var(--space-1);
  border-radius: var(--radius-xl);
}

/* ============================================
   TAB ITEM
   ============================================ */
.tab {
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all var(--duration-200) var(--ease-in-out);
  position: relative;
}

.tab:hover {
  color: var(--text-primary);
}

.tab.active {
  color: var(--interactive-default);
  border-bottom-color: var(--interactive-default);
}

/* Animated underline */
.tab::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 50%;
  width: 0;
  height: 2px;
  background: var(--interactive-default);
  transition: all var(--duration-200) var(--ease-out);
  transform: translateX(-50%);
}

.tab.active::after {
  width: 100%;
}

/* ============================================
   PILL TABS
   ============================================ */
.tabs-pills .tab {
  border-bottom: none;
  border-radius: var(--radius-lg);
  padding: var(--space-2) var(--space-4);
}

.tabs-pills .tab.active {
  background: var(--bg-elevated);
  color: var(--text-primary);
  box-shadow: var(--shadow-dark-sm);
}

.tabs-pills .tab::after {
  display: none;
}

/* ============================================
   TAB PANELS
   ============================================ */
.tab-panels {
  position: relative;
}

.tab-panel {
  display: none;
  animation: fadeIn var(--duration-200) var(--ease-out);
}

.tab-panel.active {
  display: block;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ============================================
   FILTER TABS (Horizontal scroll on mobile)
   ============================================ */
.filter-tabs {
  display: flex;
  gap: var(--space-2);
  overflow-x: auto;
  padding-bottom: var(--space-2);
  scrollbar-width: none;
}

.filter-tabs::-webkit-scrollbar {
  display: none;
}

.filter-tab {
  flex-shrink: 0;
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
  background: var(--bg-glass);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all var(--duration-200) var(--ease-in-out);
  white-space: nowrap;
}

.filter-tab:hover {
  background: var(--bg-glass-hover);
  border-color: var(--border-medium);
}

.filter-tab.active {
  background: var(--interactive-default);
  border-color: var(--interactive-default);
  color: white;
}
```

**Acceptance Criteria**:
- [ ] Tab list container
- [ ] Tab items with hover/active states
- [ ] Animated underline effect
- [ ] Pill-style tabs variant
- [ ] Tab panel containers with fade animation
- [ ] Filter tabs (horizontal scroll)

---

### Task 7: Progress Components (`_progress.css`)

**File**: `frontend/css/components/_progress.css`

```css
/**
 * Progress & Meter Components
 */

/* ============================================
   PROGRESS BAR
   ============================================ */
.progress {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width var(--duration-500) var(--ease-out);
  position: relative;
}

.progress-fill-primary {
  background: var(--gradient-primary);
}

.progress-fill-success {
  background: var(--gradient-success);
}

.progress-fill-warning {
  background: var(--gradient-warning);
}

.progress-fill-danger {
  background: var(--gradient-danger);
}

/* Shimmer effect */
.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.3),
    transparent
  );
  animation: progress-shimmer 2s infinite;
}

@keyframes progress-shimmer {
  100% { left: 100%; }
}

/* ============================================
   CONVICTION BAR
   ============================================ */
.conviction-bar {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.conviction-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 1s var(--ease-out);
}

.conviction-fill.high {
  background: var(--gradient-success);
}

.conviction-fill.medium {
  background: var(--gradient-warning);
}

.conviction-fill.low {
  background: var(--gradient-danger);
}

.conviction-fill.table-pounding {
  background: var(--gradient-primary);
}

/* ============================================
   CONFLUENCE METER
   ============================================ */
.confluence-meter {
  position: relative;
  width: 100%;
  height: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.confluence-fill {
  height: 100%;
  border-radius: var(--radius-full);
  background: linear-gradient(90deg,
    var(--color-success-500) 0%,
    var(--color-primary-500) 50%,
    var(--color-purple-500) 100%
  );
  transition: width 1.5s var(--ease-out);
  position: relative;
}

.confluence-fill::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  animation: progress-shimmer 2s infinite;
}

.confluence-score {
  position: absolute;
  right: var(--space-3);
  top: 50%;
  transform: translateY(-50%);
  font-size: var(--text-xs);
  font-weight: var(--font-bold);
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

/* ============================================
   CIRCULAR PROGRESS
   ============================================ */
.progress-circle {
  position: relative;
  width: 60px;
  height: 60px;
}

.progress-circle svg {
  transform: rotate(-90deg);
}

.progress-circle-bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.1);
  stroke-width: 4;
}

.progress-circle-fill {
  fill: none;
  stroke: var(--interactive-default);
  stroke-width: 4;
  stroke-linecap: round;
  transition: stroke-dashoffset var(--duration-500) var(--ease-out);
}

.progress-circle-value {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  font-weight: var(--font-bold);
  color: var(--text-primary);
}

/* ============================================
   STEP PROGRESS
   ============================================ */
.steps {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.step {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.step-indicator {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  background: var(--bg-glass);
  border: 2px solid var(--border-medium);
  color: var(--text-secondary);
  transition: all var(--duration-200) var(--ease-in-out);
}

.step.active .step-indicator {
  background: var(--interactive-default);
  border-color: var(--interactive-default);
  color: white;
}

.step.completed .step-indicator {
  background: var(--status-success);
  border-color: var(--status-success);
  color: white;
}

.step-connector {
  flex: 1;
  height: 2px;
  background: var(--border-medium);
  min-width: 20px;
}

.step.completed + .step .step-connector,
.step.completed .step-connector {
  background: var(--status-success);
}
```

**Acceptance Criteria**:
- [ ] Linear progress bar
- [ ] Progress bar variants (primary, success, warning, danger)
- [ ] Shimmer animation effect
- [ ] Conviction bar
- [ ] Confluence meter
- [ ] Circular progress
- [ ] Step progress indicator

---

### Task 8: Loader Components (`_loaders.css`)

**File**: `frontend/css/components/_loaders.css`

```css
/**
 * Loading & Skeleton Components
 */

/* ============================================
   SPINNER
   ============================================ */
.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-left-color: var(--interactive-default);
  border-radius: 50%;
  animation: spinner 0.8s linear infinite;
}

@keyframes spinner {
  to { transform: rotate(360deg); }
}

.spinner-sm {
  width: 16px;
  height: 16px;
  border-width: 2px;
}

.spinner-lg {
  width: 40px;
  height: 40px;
  border-width: 4px;
}

/* ============================================
   DOTS LOADER
   ============================================ */
.dots-loader {
  display: flex;
  gap: var(--space-1);
}

.dots-loader span {
  width: 8px;
  height: 8px;
  background: var(--interactive-default);
  border-radius: 50%;
  animation: dots-bounce 1.4s ease-in-out infinite;
}

.dots-loader span:nth-child(1) { animation-delay: 0s; }
.dots-loader span:nth-child(2) { animation-delay: 0.16s; }
.dots-loader span:nth-child(3) { animation-delay: 0.32s; }

@keyframes dots-bounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* ============================================
   PULSE LOADER
   ============================================ */
.pulse-loader {
  width: 40px;
  height: 40px;
  background: var(--interactive-default);
  border-radius: 50%;
  animation: pulse-scale 1.2s ease-in-out infinite;
}

@keyframes pulse-scale {
  0% {
    transform: scale(0);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 0;
  }
}

/* ============================================
   SKELETON LOADING
   ============================================ */
.skeleton {
  background: linear-gradient(
    90deg,
    var(--bg-elevated) 25%,
    rgba(255, 255, 255, 0.08) 50%,
    var(--bg-elevated) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s ease-in-out infinite;
  border-radius: var(--radius-md);
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.skeleton-text {
  height: 16px;
  margin-bottom: var(--space-2);
}

.skeleton-text:last-child {
  width: 60%;
}

.skeleton-title {
  height: 24px;
  width: 40%;
  margin-bottom: var(--space-3);
}

.skeleton-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

.skeleton-card {
  height: 120px;
  border-radius: var(--radius-2xl);
}

.skeleton-badge {
  height: 24px;
  width: 80px;
  border-radius: var(--radius-full);
}

/* ============================================
   FULL PAGE LOADER
   ============================================ */
.page-loader {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: var(--space-4);
  background: var(--bg-base);
  z-index: var(--z-modal);
}

.page-loader-logo {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--interactive-default);
  animation: fade-pulse 2s ease-in-out infinite;
}

@keyframes fade-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* ============================================
   INLINE LOADER
   ============================================ */
.inline-loader {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

/* ============================================
   CARD SKELETON
   ============================================ */
.skeleton-kpi-card {
  padding: var(--space-5);
  background: var(--bg-glass);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-2xl);
}

.skeleton-kpi-card .skeleton-text {
  width: 40%;
  height: 12px;
  margin-bottom: var(--space-3);
}

.skeleton-kpi-card .skeleton-title {
  width: 60%;
  height: 32px;
  margin-bottom: var(--space-4);
}

.skeleton-kpi-card .skeleton-bar {
  height: 40px;
  width: 100%;
  border-radius: var(--radius-md);
}
```

**Acceptance Criteria**:
- [ ] Spinner loader (multiple sizes)
- [ ] Dots loader animation
- [ ] Pulse loader
- [ ] Skeleton loading states
- [ ] Skeleton variants (text, title, avatar, card, badge)
- [ ] Full page loader
- [ ] Inline loader
- [ ] KPI card skeleton

---

### Task 9: Toast Components (`_toasts.css`)

**File**: `frontend/css/components/_toasts.css`

```css
/**
 * Toast Notification Components
 */

/* ============================================
   TOAST CONTAINER
   ============================================ */
.toast-container {
  position: fixed;
  bottom: var(--space-6);
  right: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  z-index: var(--z-toast);
  pointer-events: none;
}

.toast-container.top-right {
  bottom: auto;
  top: var(--space-6);
}

.toast-container.top-left {
  bottom: auto;
  top: var(--space-6);
  right: auto;
  left: var(--space-6);
}

.toast-container.bottom-left {
  right: auto;
  left: var(--space-6);
}

/* ============================================
   TOAST
   ============================================ */
.toast {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  min-width: 300px;
  max-width: 420px;
  padding: var(--space-4);
  background: var(--bg-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-dark-lg);
  pointer-events: auto;
  animation: toast-enter 0.4s var(--ease-bounce);
}

@keyframes toast-enter {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.toast.exiting {
  animation: toast-exit 0.3s var(--ease-in) forwards;
}

@keyframes toast-exit {
  to {
    opacity: 0;
    transform: translateX(100%);
  }
}

/* ============================================
   TOAST VARIANTS
   ============================================ */
.toast-success {
  border-left: 4px solid var(--status-success);
}

.toast-warning {
  border-left: 4px solid var(--status-warning);
}

.toast-danger {
  border-left: 4px solid var(--status-danger);
}

.toast-info {
  border-left: 4px solid var(--status-info);
}

/* ============================================
   TOAST CONTENT
   ============================================ */
.toast-icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-lg);
}

.toast-success .toast-icon { color: var(--status-success); }
.toast-warning .toast-icon { color: var(--status-warning); }
.toast-danger .toast-icon { color: var(--status-danger); }
.toast-info .toast-icon { color: var(--status-info); }

.toast-content {
  flex: 1;
  min-width: 0;
}

.toast-title {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin-bottom: var(--space-1);
}

.toast-message {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: var(--leading-normal);
}

.toast-close {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: all var(--duration-150) var(--ease-in-out);
}

.toast-close:hover {
  background: var(--bg-glass-hover);
  color: var(--text-primary);
}

/* ============================================
   TOAST PROGRESS
   ============================================ */
.toast-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 0 0 var(--radius-xl) var(--radius-xl);
  overflow: hidden;
}

.toast-progress-bar {
  height: 100%;
  background: var(--interactive-default);
  animation: toast-progress 5s linear forwards;
}

.toast-success .toast-progress-bar { background: var(--status-success); }
.toast-warning .toast-progress-bar { background: var(--status-warning); }
.toast-danger .toast-progress-bar { background: var(--status-danger); }

@keyframes toast-progress {
  from { width: 100%; }
  to { width: 0%; }
}

/* ============================================
   MOBILE TOAST
   ============================================ */
@media (max-width: 640px) {
  .toast-container {
    left: var(--space-4);
    right: var(--space-4);
    bottom: var(--space-4);
  }

  .toast {
    min-width: auto;
    max-width: none;
    width: 100%;
  }
}
```

**Acceptance Criteria**:
- [ ] Toast container positioning
- [ ] Toast variants (success, warning, danger, info)
- [ ] Toast enter/exit animations
- [ ] Toast with icon
- [ ] Toast progress bar
- [ ] Toast close button
- [ ] Mobile responsive

---

### Task 10: Ripple Effect JavaScript

**File**: `frontend/js/components/ripple.js`

```javascript
/**
 * Ripple Effect for Buttons
 * Adds material-design style ripple on click
 */

function createRipple(event) {
  const button = event.currentTarget;

  // Only apply to buttons with the class
  if (!button.classList.contains('btn')) return;

  const ripple = document.createElement('span');
  ripple.classList.add('ripple');

  const rect = button.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height);
  const x = event.clientX - rect.left - size / 2;
  const y = event.clientY - rect.top - size / 2;

  ripple.style.width = ripple.style.height = `${size}px`;
  ripple.style.left = `${x}px`;
  ripple.style.top = `${y}px`;

  button.appendChild(ripple);

  ripple.addEventListener('animationend', () => {
    ripple.remove();
  });
}

// Initialize ripple effect on all buttons
function initRipples() {
  document.querySelectorAll('.btn').forEach(button => {
    button.addEventListener('click', createRipple);
  });
}

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initRipples);
} else {
  initRipples();
}

// Export for manual initialization
window.initRipples = initRipples;
```

**Acceptance Criteria**:
- [ ] Ripple spawns at click position
- [ ] Ripple size adapts to button size
- [ ] Ripple cleans up after animation
- [ ] Auto-initializes on page load
- [ ] Can be manually re-initialized

---

## Testing Checklist

- [ ] All components render correctly
- [ ] All interactive states work (hover, focus, active, disabled)
- [ ] Components are keyboard accessible
- [ ] Components work in all supported browsers
- [ ] Dark theme displays correctly
- [ ] Mobile responsive behavior

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Component CSS size (gzipped) | < 15KB |
| Number of component variants | 50+ |
| Accessibility coverage | 100% |
| Browser compatibility | 98%+ |

---

*Created: December 2025*
*Author: Claude Code Assistant*
