# PRD-030: Animations & Micro-interactions

## Overview
This PRD defines the animation system and micro-interactions that will bring the Macro Confluence Hub interface to life. These animations enhance user experience by providing visual feedback, guiding attention, and creating a polished, professional feel.

**Dependencies**: PRD-027 (Design System), PRD-028 (Components), PRD-029 (Layout)

---

## Animation Principles

### Core Guidelines
1. **Purpose-Driven**: Every animation serves a purpose (feedback, guidance, delight)
2. **Performant**: Use `transform` and `opacity` only (GPU-accelerated)
3. **Subtle**: Animations enhance, never distract
4. **Accessible**: Respect `prefers-reduced-motion`
5. **Consistent**: Use unified timing and easing functions

### Timing Standards
```
--duration-instant: 100ms   /* Micro-feedback (ripples, hovers) */
--duration-fast: 200ms      /* Quick transitions (buttons, toggles) */
--duration-normal: 300ms    /* Standard transitions (cards, modals) */
--duration-slow: 500ms      /* Emphasis animations (page transitions) */
--duration-slower: 800ms    /* Dramatic reveals (charts, loading) */
```

### Easing Functions
```
--ease-out: cubic-bezier(0.0, 0.0, 0.2, 1)      /* Entering elements */
--ease-in: cubic-bezier(0.4, 0.0, 1, 1)          /* Exiting elements */
--ease-in-out: cubic-bezier(0.4, 0.0, 0.2, 1)    /* Moving elements */
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55) /* Playful */
--ease-smooth: cubic-bezier(0.25, 0.1, 0.25, 1)  /* Natural feel */
```

---

## Task 1: Animation Utilities CSS

**File**: `frontend/css/animations/_utilities.css`

```css
/* ============================================
   Animation Utilities
   Reusable animation classes and keyframes
   ============================================ */

/* ----- Timing Variables ----- */
:root {
  /* Durations */
  --duration-instant: 100ms;
  --duration-fast: 200ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;
  --duration-slower: 800ms;

  /* Easing */
  --ease-out: cubic-bezier(0.0, 0.0, 0.2, 1);
  --ease-in: cubic-bezier(0.4, 0.0, 1, 1);
  --ease-in-out: cubic-bezier(0.4, 0.0, 0.2, 1);
  --ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
  --ease-smooth: cubic-bezier(0.25, 0.1, 0.25, 1);
  --ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

/* ----- Base Transition Classes ----- */
.transition-none { transition: none !important; }
.transition-all { transition: all var(--duration-normal) var(--ease-smooth); }
.transition-colors { transition: color, background-color, border-color var(--duration-fast) var(--ease-smooth); }
.transition-opacity { transition: opacity var(--duration-normal) var(--ease-smooth); }
.transition-transform { transition: transform var(--duration-normal) var(--ease-out); }
.transition-shadow { transition: box-shadow var(--duration-fast) var(--ease-smooth); }

/* ----- Duration Modifiers ----- */
.duration-instant { transition-duration: var(--duration-instant) !important; }
.duration-fast { transition-duration: var(--duration-fast) !important; }
.duration-normal { transition-duration: var(--duration-normal) !important; }
.duration-slow { transition-duration: var(--duration-slow) !important; }
.duration-slower { transition-duration: var(--duration-slower) !important; }

/* ----- Easing Modifiers ----- */
.ease-out { transition-timing-function: var(--ease-out) !important; }
.ease-in { transition-timing-function: var(--ease-in) !important; }
.ease-in-out { transition-timing-function: var(--ease-in-out) !important; }
.ease-bounce { transition-timing-function: var(--ease-bounce) !important; }
.ease-spring { transition-timing-function: var(--ease-spring) !important; }

/* ----- Delay Classes ----- */
.delay-100 { transition-delay: 100ms; animation-delay: 100ms; }
.delay-200 { transition-delay: 200ms; animation-delay: 200ms; }
.delay-300 { transition-delay: 300ms; animation-delay: 300ms; }
.delay-500 { transition-delay: 500ms; animation-delay: 500ms; }

/* ----- Keyframe Animations ----- */

/* Fade */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}

/* Scale */
@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes scaleOut {
  from {
    opacity: 1;
    transform: scale(1);
  }
  to {
    opacity: 0;
    transform: scale(0.9);
  }
}

/* Slide */
@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Bounce */
@keyframes bounceIn {
  0% {
    opacity: 0;
    transform: scale(0.3);
  }
  50% {
    transform: scale(1.05);
  }
  70% {
    transform: scale(0.9);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

/* Pulse */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

@keyframes pulseScale {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

/* Shake */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
  20%, 40%, 60%, 80% { transform: translateX(4px); }
}

/* Glow */
@keyframes glow {
  0%, 100% {
    box-shadow: 0 0 5px var(--color-accent-primary);
  }
  50% {
    box-shadow: 0 0 20px var(--color-accent-primary),
                0 0 30px var(--color-accent-primary);
  }
}

/* Shimmer (for loading states) */
@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

/* Spin */
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Float */
@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

/* ----- Animation Classes ----- */
.animate-fade-in { animation: fadeIn var(--duration-normal) var(--ease-out) forwards; }
.animate-fade-out { animation: fadeOut var(--duration-normal) var(--ease-in) forwards; }
.animate-scale-in { animation: scaleIn var(--duration-normal) var(--ease-out) forwards; }
.animate-scale-out { animation: scaleOut var(--duration-normal) var(--ease-in) forwards; }
.animate-slide-up { animation: slideInUp var(--duration-normal) var(--ease-out) forwards; }
.animate-slide-down { animation: slideInDown var(--duration-normal) var(--ease-out) forwards; }
.animate-slide-left { animation: slideInLeft var(--duration-normal) var(--ease-out) forwards; }
.animate-slide-right { animation: slideInRight var(--duration-normal) var(--ease-out) forwards; }
.animate-bounce-in { animation: bounceIn var(--duration-slow) var(--ease-bounce) forwards; }
.animate-pulse { animation: pulse 2s var(--ease-in-out) infinite; }
.animate-pulse-scale { animation: pulseScale 2s var(--ease-in-out) infinite; }
.animate-shake { animation: shake var(--duration-slow) var(--ease-in-out); }
.animate-glow { animation: glow 2s var(--ease-in-out) infinite; }
.animate-shimmer {
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.1) 50%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
.animate-spin { animation: spin 1s linear infinite; }
.animate-float { animation: float 3s var(--ease-in-out) infinite; }

/* ----- Reduced Motion ----- */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Task 2: Page Transitions

**File**: `frontend/css/animations/_page-transitions.css`

```css
/* ============================================
   Page Transitions
   Smooth transitions between views and tabs
   ============================================ */

/* ----- View Container ----- */
.view-container {
  position: relative;
  overflow: hidden;
}

/* ----- Tab Content Transitions ----- */
.tab-panel {
  opacity: 0;
  transform: translateY(10px);
  transition:
    opacity var(--duration-normal) var(--ease-out),
    transform var(--duration-normal) var(--ease-out);
  pointer-events: none;
}

.tab-panel[aria-hidden="false"],
.tab-panel.active {
  opacity: 1;
  transform: translateY(0);
  pointer-events: auto;
}

/* ----- Staggered Content Entry ----- */
.stagger-container > * {
  opacity: 0;
  transform: translateY(20px);
}

.stagger-container.animate > *:nth-child(1) { animation: slideInUp var(--duration-normal) var(--ease-out) 0ms forwards; }
.stagger-container.animate > *:nth-child(2) { animation: slideInUp var(--duration-normal) var(--ease-out) 50ms forwards; }
.stagger-container.animate > *:nth-child(3) { animation: slideInUp var(--duration-normal) var(--ease-out) 100ms forwards; }
.stagger-container.animate > *:nth-child(4) { animation: slideInUp var(--duration-normal) var(--ease-out) 150ms forwards; }
.stagger-container.animate > *:nth-child(5) { animation: slideInUp var(--duration-normal) var(--ease-out) 200ms forwards; }
.stagger-container.animate > *:nth-child(6) { animation: slideInUp var(--duration-normal) var(--ease-out) 250ms forwards; }
.stagger-container.animate > *:nth-child(7) { animation: slideInUp var(--duration-normal) var(--ease-out) 300ms forwards; }
.stagger-container.animate > *:nth-child(8) { animation: slideInUp var(--duration-normal) var(--ease-out) 350ms forwards; }

/* ----- Modal Transitions ----- */
.modal-backdrop {
  opacity: 0;
  transition: opacity var(--duration-normal) var(--ease-out);
}

.modal-backdrop.active {
  opacity: 1;
}

.modal-content {
  opacity: 0;
  transform: scale(0.95) translateY(20px);
  transition:
    opacity var(--duration-normal) var(--ease-out),
    transform var(--duration-normal) var(--ease-out);
}

.modal-backdrop.active .modal-content {
  opacity: 1;
  transform: scale(1) translateY(0);
}

/* ----- Drawer Transitions ----- */
.drawer {
  transform: translateX(-100%);
  transition: transform var(--duration-normal) var(--ease-out);
}

.drawer.open {
  transform: translateX(0);
}

.drawer-right {
  transform: translateX(100%);
}

.drawer-right.open {
  transform: translateX(0);
}

/* ----- Accordion/Collapse ----- */
.collapse-content {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows var(--duration-normal) var(--ease-out);
}

.collapse-content.expanded {
  grid-template-rows: 1fr;
}

.collapse-content > .collapse-inner {
  overflow: hidden;
}

/* ----- Page Load Animation ----- */
.page-loading {
  opacity: 0;
}

.page-ready {
  animation: fadeIn var(--duration-slow) var(--ease-out) forwards;
}

/* Hero section entrance */
.hero-section {
  opacity: 0;
  transform: translateY(30px);
}

.hero-section.animate {
  animation: slideInUp var(--duration-slow) var(--ease-out) forwards;
}

/* KPI cards stagger entrance */
.kpi-grid .kpi-card {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

.kpi-grid.animate .kpi-card:nth-child(1) { animation: kpiEnter var(--duration-normal) var(--ease-spring) 100ms forwards; }
.kpi-grid.animate .kpi-card:nth-child(2) { animation: kpiEnter var(--duration-normal) var(--ease-spring) 150ms forwards; }
.kpi-grid.animate .kpi-card:nth-child(3) { animation: kpiEnter var(--duration-normal) var(--ease-spring) 200ms forwards; }
.kpi-grid.animate .kpi-card:nth-child(4) { animation: kpiEnter var(--duration-normal) var(--ease-spring) 250ms forwards; }
.kpi-grid.animate .kpi-card:nth-child(5) { animation: kpiEnter var(--duration-normal) var(--ease-spring) 300ms forwards; }

@keyframes kpiEnter {
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
```

---

## Task 3: Component Micro-interactions

**File**: `frontend/css/animations/_microinteractions.css`

```css
/* ============================================
   Micro-interactions
   Subtle feedback animations for components
   ============================================ */

/* ----- Button Interactions ----- */
.btn {
  position: relative;
  overflow: hidden;
  transition:
    transform var(--duration-fast) var(--ease-out),
    box-shadow var(--duration-fast) var(--ease-out),
    background-color var(--duration-fast) var(--ease-out);
}

.btn:hover {
  transform: translateY(-2px);
}

.btn:active {
  transform: translateY(0) scale(0.98);
}

/* Button loading state */
.btn.loading {
  pointer-events: none;
  opacity: 0.8;
}

.btn.loading::after {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Success/Error feedback */
.btn.success {
  animation: successPulse var(--duration-normal) var(--ease-out);
}

.btn.error {
  animation: shake var(--duration-slow) var(--ease-in-out);
}

@keyframes successPulse {
  0% { box-shadow: 0 0 0 0 var(--color-success); }
  50% { box-shadow: 0 0 0 8px transparent; }
  100% { box-shadow: 0 0 0 0 transparent; }
}

/* ----- Card Interactions ----- */
.card-interactive {
  transition:
    transform var(--duration-fast) var(--ease-out),
    box-shadow var(--duration-fast) var(--ease-out);
  cursor: pointer;
}

.card-interactive:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.card-interactive:active {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

/* Card shine effect on hover */
.card-shine {
  position: relative;
  overflow: hidden;
}

.card-shine::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.1),
    transparent
  );
  transition: left var(--duration-slow) var(--ease-out);
}

.card-shine:hover::before {
  left: 100%;
}

/* ----- Toggle Switch ----- */
.toggle-switch {
  position: relative;
  width: 48px;
  height: 24px;
  background: var(--color-bg-tertiary);
  border-radius: 12px;
  cursor: pointer;
  transition: background-color var(--duration-fast) var(--ease-out);
}

.toggle-switch::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  transition: transform var(--duration-fast) var(--ease-spring);
  box-shadow: var(--shadow-sm);
}

.toggle-switch.active {
  background: var(--color-accent-primary);
}

.toggle-switch.active::after {
  transform: translateX(24px);
}

/* ----- Checkbox Animation ----- */
.checkbox-custom {
  position: relative;
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border-primary);
  border-radius: var(--radius-sm);
  transition:
    background-color var(--duration-fast) var(--ease-out),
    border-color var(--duration-fast) var(--ease-out);
}

.checkbox-custom::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 6px;
  width: 5px;
  height: 10px;
  border: 2px solid white;
  border-top: none;
  border-left: none;
  transform: rotate(45deg) scale(0);
  transition: transform var(--duration-fast) var(--ease-spring);
}

.checkbox-custom.checked {
  background: var(--color-accent-primary);
  border-color: var(--color-accent-primary);
}

.checkbox-custom.checked::after {
  transform: rotate(45deg) scale(1);
}

/* ----- Input Focus ----- */
.input-animated {
  position: relative;
  transition:
    border-color var(--duration-fast) var(--ease-out),
    box-shadow var(--duration-fast) var(--ease-out);
}

.input-animated:focus {
  border-color: var(--color-accent-primary);
  box-shadow: 0 0 0 3px rgba(var(--color-accent-primary-rgb), 0.2);
}

/* Floating label */
.input-group {
  position: relative;
}

.input-group .floating-label {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-tertiary);
  pointer-events: none;
  transition:
    transform var(--duration-fast) var(--ease-out),
    font-size var(--duration-fast) var(--ease-out),
    color var(--duration-fast) var(--ease-out);
}

.input-group input:focus + .floating-label,
.input-group input:not(:placeholder-shown) + .floating-label {
  transform: translateY(-28px);
  font-size: 12px;
  color: var(--color-accent-primary);
}

/* ----- Badge Pulse ----- */
.badge-notification {
  position: relative;
}

.badge-notification::after {
  content: '';
  position: absolute;
  top: -2px;
  right: -2px;
  width: 8px;
  height: 8px;
  background: var(--color-error);
  border-radius: 50%;
  animation: badgePulse 2s var(--ease-in-out) infinite;
}

@keyframes badgePulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.7;
  }
}

/* ----- Tooltip ----- */
.tooltip {
  position: relative;
}

.tooltip::after {
  content: attr(data-tooltip);
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(10px);
  padding: 6px 12px;
  background: var(--color-bg-elevated);
  color: var(--color-text-primary);
  border-radius: var(--radius-sm);
  font-size: 12px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition:
    opacity var(--duration-fast) var(--ease-out),
    transform var(--duration-fast) var(--ease-out);
  box-shadow: var(--shadow-lg);
}

.tooltip:hover::after {
  opacity: 1;
  transform: translateX(-50%) translateY(-8px);
}

/* ----- Progress Bar Animation ----- */
.progress-bar {
  position: relative;
  overflow: hidden;
}

.progress-bar-fill {
  transition: width var(--duration-slow) var(--ease-out);
}

.progress-bar-fill.animate {
  position: relative;
}

.progress-bar-fill.animate::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.3),
    transparent
  );
  animation: shimmer 1.5s infinite;
}

/* ----- Sentiment Indicator Pulse ----- */
.sentiment-bullish {
  animation: sentimentPulse 3s var(--ease-in-out) infinite;
}

@keyframes sentimentPulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(16, 185, 129, 0);
  }
}

.sentiment-bearish {
  animation: sentimentPulseBear 3s var(--ease-in-out) infinite;
}

@keyframes sentimentPulseBear {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(239, 68, 68, 0);
  }
}

/* ----- Refresh/Sync Icon ----- */
.icon-refresh {
  transition: transform var(--duration-normal) var(--ease-out);
}

.icon-refresh.syncing {
  animation: spin 1s linear infinite;
}

.icon-refresh:hover {
  transform: rotate(180deg);
}

/* ----- Expandable Content ----- */
.expand-icon {
  transition: transform var(--duration-fast) var(--ease-out);
}

.expanded .expand-icon {
  transform: rotate(180deg);
}
```

---

## Task 4: Loading States & Skeletons

**File**: `frontend/css/animations/_loading.css`

```css
/* ============================================
   Loading States & Skeleton Screens
   Smooth loading experiences
   ============================================ */

/* ----- Skeleton Base ----- */
.skeleton {
  position: relative;
  overflow: hidden;
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
}

.skeleton::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.05) 50%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

/* Skeleton Variants */
.skeleton-text {
  height: 16px;
  border-radius: var(--radius-sm);
}

.skeleton-text-sm {
  height: 12px;
  border-radius: var(--radius-xs);
}

.skeleton-text-lg {
  height: 24px;
  border-radius: var(--radius-sm);
}

.skeleton-heading {
  height: 32px;
  width: 60%;
  border-radius: var(--radius-sm);
}

.skeleton-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

.skeleton-button {
  height: 40px;
  width: 120px;
  border-radius: var(--radius-md);
}

.skeleton-card {
  height: 200px;
  border-radius: var(--radius-lg);
}

.skeleton-kpi {
  height: 100px;
  border-radius: var(--radius-lg);
}

/* ----- Skeleton Card Layout ----- */
.skeleton-card-content {
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.skeleton-card-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.skeleton-card-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

/* ----- Loading Spinner Variants ----- */

/* Simple spinner */
.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--color-bg-tertiary);
  border-top-color: var(--color-accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
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

/* Dots loader */
.loader-dots {
  display: flex;
  gap: 6px;
}

.loader-dots span {
  width: 8px;
  height: 8px;
  background: var(--color-accent-primary);
  border-radius: 50%;
  animation: dotBounce 1.4s ease-in-out infinite;
}

.loader-dots span:nth-child(1) { animation-delay: 0s; }
.loader-dots span:nth-child(2) { animation-delay: 0.16s; }
.loader-dots span:nth-child(3) { animation-delay: 0.32s; }

@keyframes dotBounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* Pulse loader */
.loader-pulse {
  width: 40px;
  height: 40px;
  background: var(--color-accent-primary);
  border-radius: 50%;
  animation: loaderPulse 1.5s ease-in-out infinite;
}

@keyframes loaderPulse {
  0% {
    transform: scale(0);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 0;
  }
}

/* Bar loader */
.loader-bar {
  width: 100%;
  height: 4px;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
}

.loader-bar::after {
  content: '';
  display: block;
  width: 40%;
  height: 100%;
  background: var(--color-accent-primary);
  border-radius: 2px;
  animation: barSlide 1.5s ease-in-out infinite;
}

@keyframes barSlide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}

/* ----- Page Loading Overlay ----- */
.page-loader {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-bg-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: var(--space-4);
  z-index: 9999;
  opacity: 1;
  transition: opacity var(--duration-normal) var(--ease-out);
}

.page-loader.hidden {
  opacity: 0;
  pointer-events: none;
}

.page-loader-logo {
  animation: float 2s var(--ease-in-out) infinite;
}

.page-loader-text {
  color: var(--color-text-secondary);
  animation: pulse 2s var(--ease-in-out) infinite;
}

/* ----- Content Placeholder ----- */
.content-loading {
  position: relative;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.content-loading::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
  opacity: 0.5;
}

/* ----- Lazy Image Loading ----- */
.img-lazy {
  background: var(--color-bg-secondary);
  transition: opacity var(--duration-normal) var(--ease-out);
}

.img-lazy:not([src]) {
  opacity: 0;
}

.img-lazy[src] {
  opacity: 1;
}

/* ----- Data Refresh Indicator ----- */
.refresh-indicator {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%) translateY(-100%);
  padding: var(--space-2) var(--space-4);
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border-radius: var(--radius-full);
  border: 1px solid var(--glass-border);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  transition: transform var(--duration-normal) var(--ease-spring);
  z-index: 100;
}

.refresh-indicator.visible {
  transform: translateX(-50%) translateY(0);
}

.refresh-indicator .spinner {
  width: 16px;
  height: 16px;
}
```

---

## Task 5: Animation JavaScript Controller

**File**: `frontend/js/animations.js`

```javascript
/**
 * Animation Controller
 * Manages page animations, transitions, and micro-interactions
 */

const AnimationController = {
  // Configuration
  config: {
    observerThreshold: 0.1,
    staggerDelay: 50,
    reducedMotion: false
  },

  /**
   * Initialize animation system
   */
  init() {
    // Check for reduced motion preference
    this.config.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Listen for preference changes
    window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
      this.config.reducedMotion = e.matches;
    });

    // Setup intersection observer for scroll animations
    this.setupScrollAnimations();

    // Setup ripple effects
    this.setupRippleEffects();

    // Setup page load animations
    this.animatePageLoad();

    // Setup tab transitions
    this.setupTabTransitions();

    console.log('[Animations] Controller initialized');
  },

  /**
   * Setup intersection observer for scroll-triggered animations
   */
  setupScrollAnimations() {
    if (this.config.reducedMotion) return;

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate');
          // Optionally unobserve after animation
          if (entry.target.dataset.animateOnce !== 'false') {
            observer.unobserve(entry.target);
          }
        }
      });
    }, {
      threshold: this.config.observerThreshold,
      rootMargin: '0px 0px -50px 0px'
    });

    // Observe elements with animation classes
    document.querySelectorAll('.stagger-container, .hero-section, .kpi-grid, [data-animate]').forEach(el => {
      observer.observe(el);
    });

    this.scrollObserver = observer;
  },

  /**
   * Setup material-design ripple effects on buttons
   */
  setupRippleEffects() {
    document.addEventListener('click', (e) => {
      const button = e.target.closest('.btn, .card-interactive, [data-ripple]');
      if (!button || this.config.reducedMotion) return;

      const ripple = document.createElement('span');
      ripple.className = 'ripple-effect';

      const rect = button.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const x = e.clientX - rect.left - size / 2;
      const y = e.clientY - rect.top - size / 2;

      ripple.style.cssText = `
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
      `;

      button.appendChild(ripple);

      // Remove ripple after animation
      ripple.addEventListener('animationend', () => {
        ripple.remove();
      });
    });
  },

  /**
   * Animate page load
   */
  animatePageLoad() {
    if (this.config.reducedMotion) {
      document.body.classList.add('page-ready');
      return;
    }

    // Wait for DOM ready
    requestAnimationFrame(() => {
      document.body.classList.remove('page-loading');
      document.body.classList.add('page-ready');

      // Trigger hero animation
      const hero = document.querySelector('.hero-section');
      if (hero) {
        setTimeout(() => hero.classList.add('animate'), 100);
      }

      // Trigger KPI grid animation
      const kpiGrid = document.querySelector('.kpi-grid');
      if (kpiGrid) {
        setTimeout(() => kpiGrid.classList.add('animate'), 300);
      }
    });
  },

  /**
   * Setup smooth tab transitions
   */
  setupTabTransitions() {
    document.querySelectorAll('[role="tab"]').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const targetId = tab.getAttribute('aria-controls');
        const targetPanel = document.getElementById(targetId);
        const currentPanel = document.querySelector('[role="tabpanel"][aria-hidden="false"]');

        if (currentPanel && targetPanel && currentPanel !== targetPanel) {
          this.transitionPanels(currentPanel, targetPanel);
        }
      });
    });
  },

  /**
   * Transition between panels with animation
   */
  transitionPanels(fromPanel, toPanel) {
    if (this.config.reducedMotion) {
      fromPanel.setAttribute('aria-hidden', 'true');
      toPanel.setAttribute('aria-hidden', 'false');
      return;
    }

    // Animate out
    fromPanel.style.opacity = '0';
    fromPanel.style.transform = 'translateY(10px)';

    setTimeout(() => {
      fromPanel.setAttribute('aria-hidden', 'true');
      fromPanel.style.cssText = '';

      // Animate in
      toPanel.setAttribute('aria-hidden', 'false');

      // Re-trigger stagger animations in new panel
      toPanel.querySelectorAll('.stagger-container').forEach(container => {
        container.classList.remove('animate');
        requestAnimationFrame(() => {
          container.classList.add('animate');
        });
      });
    }, 200);
  },

  /**
   * Animate element entrance
   */
  animateIn(element, animation = 'fade-in') {
    if (this.config.reducedMotion) {
      element.style.opacity = '1';
      return Promise.resolve();
    }

    return new Promise(resolve => {
      element.classList.add(`animate-${animation}`);
      element.addEventListener('animationend', () => {
        resolve();
      }, { once: true });
    });
  },

  /**
   * Animate element exit
   */
  animateOut(element, animation = 'fade-out') {
    if (this.config.reducedMotion) {
      element.style.opacity = '0';
      return Promise.resolve();
    }

    return new Promise(resolve => {
      element.classList.add(`animate-${animation}`);
      element.addEventListener('animationend', () => {
        element.classList.remove(`animate-${animation}`);
        resolve();
      }, { once: true });
    });
  },

  /**
   * Stagger animate children
   */
  staggerChildren(parent, animation = 'slide-up', delay = 50) {
    if (this.config.reducedMotion) return;

    const children = Array.from(parent.children);
    children.forEach((child, index) => {
      child.style.animationDelay = `${index * delay}ms`;
      child.classList.add(`animate-${animation}`);
    });
  },

  /**
   * Show success feedback on element
   */
  showSuccess(element) {
    element.classList.add('success');
    setTimeout(() => element.classList.remove('success'), 500);
  },

  /**
   * Show error feedback on element
   */
  showError(element) {
    element.classList.add('error');
    element.classList.add('animate-shake');
    setTimeout(() => {
      element.classList.remove('error', 'animate-shake');
    }, 500);
  },

  /**
   * Add loading state to button
   */
  setButtonLoading(button, loading = true) {
    if (loading) {
      button.classList.add('loading');
      button.dataset.originalText = button.textContent;
      button.textContent = '';
    } else {
      button.classList.remove('loading');
      if (button.dataset.originalText) {
        button.textContent = button.dataset.originalText;
        delete button.dataset.originalText;
      }
    }
  },

  /**
   * Show refresh indicator
   */
  showRefreshIndicator(show = true) {
    let indicator = document.querySelector('.refresh-indicator');
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.className = 'refresh-indicator';
      indicator.innerHTML = '<div class="spinner"></div><span>Updating...</span>';
      document.body.appendChild(indicator);
    }

    if (show) {
      requestAnimationFrame(() => indicator.classList.add('visible'));
    } else {
      indicator.classList.remove('visible');
    }
  },

  /**
   * Create skeleton loader
   */
  createSkeleton(type = 'card') {
    const skeleton = document.createElement('div');
    skeleton.className = `skeleton skeleton-${type}`;

    if (type === 'card') {
      skeleton.innerHTML = `
        <div class="skeleton-card-content">
          <div class="skeleton-card-header">
            <div class="skeleton skeleton-avatar"></div>
            <div class="skeleton skeleton-text" style="width: 60%"></div>
          </div>
          <div class="skeleton-card-body">
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-text" style="width: 80%"></div>
            <div class="skeleton skeleton-text" style="width: 40%"></div>
          </div>
        </div>
      `;
    }

    return skeleton;
  },

  /**
   * Replace element with skeleton, then restore
   */
  async withSkeleton(element, asyncFn) {
    const skeleton = this.createSkeleton();
    const parent = element.parentNode;

    // Store original element
    const placeholder = document.createComment('skeleton-placeholder');
    parent.insertBefore(placeholder, element);
    parent.insertBefore(skeleton, element);
    element.style.display = 'none';

    try {
      await asyncFn();
    } finally {
      // Restore original
      skeleton.remove();
      element.style.display = '';
      placeholder.remove();

      // Animate in
      this.animateIn(element, 'fade-in');
    }
  }
};

// Ripple effect CSS (injected)
const rippleStyles = document.createElement('style');
rippleStyles.textContent = `
  .ripple-effect {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.3);
    transform: scale(0);
    animation: ripple 0.6s linear;
    pointer-events: none;
  }

  @keyframes ripple {
    to {
      transform: scale(4);
      opacity: 0;
    }
  }
`;
document.head.appendChild(rippleStyles);

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => AnimationController.init());
} else {
  AnimationController.init();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AnimationController;
}
```

---

## Task 6: Animation Import File

**File**: `frontend/css/animations/animations.css`

```css
/* ============================================
   Animations Master Import
   Import all animation-related styles
   ============================================ */

@import '_utilities.css';
@import '_page-transitions.css';
@import '_microinteractions.css';
@import '_loading.css';
```

---

## Implementation Checklist

### Task 1: Animation Utilities CSS
- [ ] Create `frontend/css/animations/` directory
- [ ] Create `_utilities.css` with timing variables
- [ ] Add all keyframe definitions
- [ ] Add utility classes
- [ ] Add reduced motion support

### Task 2: Page Transitions
- [ ] Create `_page-transitions.css`
- [ ] Implement tab panel transitions
- [ ] Add staggered entry animations
- [ ] Add modal/drawer transitions
- [ ] Add page load animations

### Task 3: Component Micro-interactions
- [ ] Create `_microinteractions.css`
- [ ] Add button interactions
- [ ] Add card hover effects
- [ ] Add toggle/checkbox animations
- [ ] Add input focus effects
- [ ] Add tooltip animations

### Task 4: Loading States & Skeletons
- [ ] Create `_loading.css`
- [ ] Add skeleton base styles
- [ ] Add skeleton variants
- [ ] Add spinner variants
- [ ] Add page loader overlay
- [ ] Add refresh indicator

### Task 5: Animation JavaScript Controller
- [ ] Create `frontend/js/animations.js`
- [ ] Implement intersection observer
- [ ] Add ripple effect handler
- [ ] Add page load orchestration
- [ ] Add tab transition logic
- [ ] Add helper methods

### Task 6: Animation Import File
- [ ] Create `animations.css` master import
- [ ] Update main style.css to import animations
- [ ] Update index.html to include animations.js

---

## Animation Performance Guidelines

1. **Use GPU-accelerated properties only**:
   - `transform`
   - `opacity`
   - Avoid animating `width`, `height`, `margin`, `padding`

2. **Use `will-change` sparingly**:
   ```css
   .will-animate {
     will-change: transform, opacity;
   }
   ```

3. **Debounce scroll-triggered animations**

4. **Use `requestAnimationFrame` for JS animations**

5. **Test on low-powered devices**

---

## Accessibility Considerations

1. **Always respect `prefers-reduced-motion`**
2. **Ensure focus indicators are visible during transitions**
3. **Don't rely on animation alone for state changes**
4. **Keep animation durations under 500ms for essential UI**
5. **Provide pause controls for continuous animations**
